// frontend/src/app/admin/services/rule-run.service.ts

import { Injectable, inject, signal, computed, DestroyRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { environment } from '../../../environments/environment';
import { 
  RuleRunGroup, 
  RuleModel, 
  TriggerStatus, 
  CommitResponse, 
  RuleRunHistory 
} from '../../shared/models/rule.models';

// SSE Progress Event interface matching backend response
export interface ProgressEvent {
  runId: string;
  status: 'extracting' | 'reviewing' | 'generating' | 'publishing' | 'completed' | 'failed';
  currentStep: number;
  stepName: string;
  progress: number;
  aiEngine?: string;
  timestamp: string;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'error';

@Injectable({
  providedIn: 'root'
})
export class RuleRunService {
  private http = inject(HttpClient);
  private destroyRef = inject(DestroyRef);
  private apiUrl = `${environment.apiBaseUrl}/api/rules`;
  
  // SSE-related state using signals
  private activeEventSources = new Map<string, EventSource>();
  private progressSubject = new Subject<ProgressEvent>();
  private connectionStatusSubject = new BehaviorSubject<ConnectionStatus>('disconnected');
  
  // Public signals for reactive components
  readonly progressUpdates$ = this.progressSubject.asObservable();
  readonly connectionStatus$ = this.connectionStatusSubject.asObservable();
  
  // Reactive state signals
  readonly isConnected = signal(false);
  readonly activeConnections = signal<string[]>([]);
  readonly lastProgressUpdate = signal<ProgressEvent | null>(null);
  
  // Computed values
  readonly hasActiveConnections = computed(() => this.activeConnections().length > 0);
  readonly connectionCount = computed(() => this.activeConnections().length);

  constructor() {
    // Subscribe to connection status changes using Angular 20+ patterns
    this.connectionStatus$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(status => {
        this.isConnected.set(status === 'connected');
      });

    // Subscribe to progress updates to maintain latest state
    this.progressUpdates$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(progress => {
        this.lastProgressUpdate.set(progress);
      });

    // Cleanup all connections when service is destroyed
    this.destroyRef.onDestroy(() => {
      this.disconnectAllProgressStreams();
    });
  }

  // HTTP API methods (unchanged)
  checkTriggerEligibility(): Observable<TriggerStatus> {
    return this.http.get<TriggerStatus>(`${this.apiUrl}/trigger-eligible`);
  }

  triggerRuleRun(planId: string): Observable<{ runId: string; status: string }> {
    return this.http.post<{ runId: string; status: string }>(`${this.apiUrl}/run`, { planId });
  }

  getPendingRules(planId: string): Observable<RuleRunGroup[]> {
    return this.http.get<RuleRunGroup[]>(`${this.apiUrl}/review`, { 
      params: { plan: planId } 
    });
  }

  approveRule(ruleId: string): Observable<RuleModel> {
    return this.http.post<RuleModel>(`${this.apiUrl}/approve`, { ruleId });
  }

  rejectRule(ruleId: string): Observable<RuleModel> {
    return this.http.post<RuleModel>(`${this.apiUrl}/reject`, { ruleId });
  }

  commitRules(planId: string): Observable<CommitResponse> {
    return this.http.post<CommitResponse>(`${this.apiUrl}/commit`, { planId });
  }

  getPastRuns(planId: string): Observable<RuleRunHistory[]> {
    return this.http.get<RuleRunHistory[]>(`${this.apiUrl}/history`, { 
      params: { plan: planId } 
    });
  }

  // SSE Progress Tracking Methods with Angular 20+ optimizations

  /**
   * Connect to real-time progress stream for a specific run
   */
  connectToProgressStream(runId: string): void {
    // Close existing connection for this runId if any
    this.disconnectProgressStream(runId);
    
    const sseUrl = `${environment.apiBaseUrl}/api/rules/progress-stream/${runId}`;
    
    try {
      const eventSource = new EventSource(sseUrl);
      
      eventSource.onopen = () => {
        console.log(`SSE connected for run ${runId}`);
        this.connectionStatusSubject.next('connected');
        this.updateActiveConnections();
      };
      
      eventSource.onmessage = (event) => {
        try {
          const progressData: ProgressEvent = JSON.parse(event.data);
          console.log('Progress update received:', progressData);
          this.progressSubject.next(progressData);
          
          // Auto-close connection when completed or failed
          if (progressData.status === 'completed' || progressData.status === 'failed') {
            this.disconnectProgressStream(runId);
          }
        } catch (error) {
          console.error('Failed to parse SSE event data:', error);
          this.handleParseError(runId, error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error(`SSE connection error for run ${runId}:`, error);
        this.connectionStatusSubject.next('error');
        
        // Implement exponential backoff for reconnection
        this.handleConnectionError(runId, eventSource);
      };
      
      // Store the EventSource for cleanup
      this.activeEventSources.set(runId, eventSource);
      this.updateActiveConnections();
      
    } catch (error) {
      console.error(`Failed to create SSE connection for run ${runId}:`, error);
      this.connectionStatusSubject.next('error');
    }
  }
  
  /**
   * Disconnect progress stream for a specific run
   */
  disconnectProgressStream(runId: string): void {
    const eventSource = this.activeEventSources.get(runId);
    if (eventSource) {
      eventSource.close();
      this.activeEventSources.delete(runId);
      console.log(`SSE disconnected for run ${runId}`);
      
      this.updateActiveConnections();
      
      // Update connection status if no active connections
      if (this.activeEventSources.size === 0) {
        this.connectionStatusSubject.next('disconnected');
      }
    }
  }
  
  /**
   * Disconnect all active progress streams
   */
  disconnectAllProgressStreams(): void {
    this.activeEventSources.forEach((eventSource, runId) => {
      eventSource.close();
      console.log(`SSE disconnected for run ${runId}`);
    });
    this.activeEventSources.clear();
    this.updateActiveConnections();
    this.connectionStatusSubject.next('disconnected');
  }
  
  /**
   * Check if currently connected to progress stream for a run
   */
  isConnectedToRun(runId: string): boolean {
    const eventSource = this.activeEventSources.get(runId);
    return eventSource?.readyState === EventSource.OPEN;
  }
  
  /**
   * Get list of active run connections
   */
  getActiveConnections(): string[] {
    return Array.from(this.activeEventSources.keys());
  }

  /**
   * Get connection details for debugging
   */
  getConnectionDetails(): Record<string, { readyState: number; url: string }> {
    const details: Record<string, { readyState: number; url: string }> = {};
    this.activeEventSources.forEach((eventSource, runId) => {
      details[runId] = {
        readyState: eventSource.readyState,
        url: eventSource.url
      };
    });
    return details;
  }
  
  // Private helper methods
  
  private updateActiveConnections(): void {
    const connectionIds = Array.from(this.activeEventSources.keys());
    this.activeConnections.set(connectionIds);
  }

  private handleParseError(runId: string, error: any): void {
    console.error(`Failed to parse progress data for run ${runId}:`, error);
    // Don't disconnect on parse errors, just log them
    // The connection might recover with the next valid message
  }
  
  private handleConnectionError(runId: string, eventSource: EventSource): void {
    // Implement exponential backoff for reconnection
    let retryCount = 0;
    const maxRetries = 3;
    const baseDelay = 1000; // 1 second
    
    const reconnect = () => {
      if (retryCount >= maxRetries) {
        console.error(`Max SSE reconnection attempts reached for run ${runId}`);
        this.disconnectProgressStream(runId);
        return;
      }
      
      const delay = baseDelay * Math.pow(2, retryCount);
      retryCount++;
      
      console.log(`Attempting SSE reconnection ${retryCount}/${maxRetries} for run ${runId} in ${delay}ms`);
      
      setTimeout(() => {
        // Only attempt reconnection if the connection was closed unexpectedly
        if (eventSource.readyState === EventSource.CLOSED) {
          this.connectToProgressStream(runId);
        }
      }, delay);
    };
    
    // Only attempt reconnection if the connection was closed unexpectedly
    if (eventSource.readyState === EventSource.CLOSED) {
      reconnect();
    }
  }
  
  /**
   * Enhanced rule run trigger with automatic SSE connection
   */
  triggerRuleRunWithProgress(planId: string): Observable<{ runId: string; status: string }> {
    return new Observable(observer => {
      // First trigger the rule run
      this.triggerRuleRun(planId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (response) => {
            console.log('Rule run triggered:', response);
            
            // Automatically connect to progress stream
            this.connectToProgressStream(response.runId);
            
            observer.next(response);
            observer.complete();
          },
          error: (error) => {
            console.error('Failed to trigger rule run:', error);
            observer.error(error);
          }
        });
    });
  }

  /**
   * Reconnect to a specific run's progress stream
   */
  reconnectToRun(runId: string): void {
    console.log(`Manual reconnection requested for run ${runId}`);
    this.disconnectProgressStream(runId);
    
    // Small delay before reconnecting
    setTimeout(() => {
      this.connectToProgressStream(runId);
    }, 500);
  }

  /**
   * Health check for SSE connections
   */
  performHealthCheck(): { healthy: boolean; details: any } {
    const connections = this.getConnectionDetails();
    const healthyConnections = Object.values(connections).filter(
      conn => conn.readyState === EventSource.OPEN
    );
    
    return {
      healthy: Object.keys(connections).length === healthyConnections.length,
      details: {
        totalConnections: Object.keys(connections).length,
        healthyConnections: healthyConnections.length,
        connections: connections
      }
    };
  }

  /**
   * Angular 20+ compatible cleanup method
   * This replaces the need for ngOnDestroy in components
   */
  cleanup(): void {
    this.disconnectAllProgressStreams();
    this.progressSubject.complete();
    this.connectionStatusSubject.complete();
  }
}
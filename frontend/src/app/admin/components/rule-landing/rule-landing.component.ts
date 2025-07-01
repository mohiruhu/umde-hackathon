// frontend/src/app/admin/components/rule-landing/rule-landing.component.ts

import { Component, signal, computed, effect, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RuleRunService, ProgressEvent } from '../../services/rule-run.service';
import { TriggerStatus } from '../../../shared/models/rule.models';

interface ProgressStep {
  step: number;
  name: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  icon: string;
}

interface PastRun {
  runId: string;
  started: string;
  rules: number;
}

@Component({
  selector: 'app-rule-landing',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="container">
      <header>
        <h1>Program Rule Setup</h1>
        <p class="subtitle">Select a CMS program to review and validate extraction rules</p>
      </header>

      <!-- Connection Status Indicator -->
      @if (isRunning() && connectionStatus() !== 'disconnected') {
        <div class="connection-status" [class]="'status-' + connectionStatus()">
          @switch (connectionStatus()) {
            @case ('connected') {
              <span class="status-icon">🟢</span> Real-time updates connected
            }
            @case ('error') {
              <span class="status-icon">🔴</span> Connection error - retrying...
            }
          }
        </div>
      }

      <div class="program-select">
        <div class="form-group">
          <label for="program">Select Program:</label>
          <select 
            id="program" 
            class="dropdown"
            [formControl]="programControl"
            [disabled]="isRunning()">
            <option value="">-- Choose a program --</option>
            @for (program of programs(); track program.value) {
              <option [value]="program.value">{{ program.label }}</option>
            }
          </select>
        </div>
        <button 
          class="view-history-btn" 
          (click)="openPastRunsModal()"
          [disabled]="isRunning()">
          View Past Runs
        </button>
      </div>

      @if (showEmptyState()) {
        <div class="empty-state visible">
          {{ emptyStateMessage() }}
        </div>
      }

      <button 
        id="runBtn" 
        class="run-btn" 
        [disabled]="!canRunRule()"
        (click)="startRuleRun()">
        {{ getRunButtonText() }}
      </button>

      @if (isRunning()) {
        <div class="progress-tracker visible">
          <!-- Run Metadata -->
          <div class="run-metadata">
            <div class="run-info">
              <strong>Run ID:</strong> {{ currentRunId() }}
              @if (currentProgress(); as progress) {
                <span class="progress-percent">{{ progress.toFixed(1) }}% complete</span>
              }
            </div>
            @if (currentAiEngine(); as engine) {
              <div class="ai-engine">
                <strong>Current Engine:</strong> {{ engine }}
              </div>
            }
          </div>

          <!-- Progress Steps -->
          @for (step of progressSteps(); track step.step) {
            <div 
              class="progress-step"
              [class.complete]="step.status === 'complete'"
              [class.active]="step.status === 'active'"
              [class.pending]="step.status === 'pending'"
              [class.error]="step.status === 'error'">
              <span class="progress-icon" [innerHTML]="step.icon"></span>
              <span>{{ step.name }}</span>
              @if (step.status === 'active' && currentProgress(); as progress) {
                <span class="step-progress">({{ progress.toFixed(0) }}%)</span>
              }
            </div>
          }

          <!-- Error Handling -->
          @if (hasError()) {
            <div class="error-message">
              <span class="error-icon">⚠️</span>
              {{ errorMessage() }}
              <button class="retry-btn" (click)="retryConnection()">Retry Connection</button>
            </div>
          }
        </div>
      }
    </div>

    <!-- Past Runs Modal -->
    @if (showModal()) {
      <div class="modal-overlay" (click)="closePastRunsModal()"></div>
      <div class="modal visible">
        <div class="modal-header">
          <h2 class="modal-title">Past Rule Runs</h2>
          <button class="modal-close" (click)="closePastRunsModal()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="modal-search">
            <input 
              type="text" 
              class="search-input" 
              placeholder="Search runs..."
              [formControl]="searchControl">
            <a href="#" class="export-link">
              <span>📥</span> Export
            </a>
          </div>
          <div id="runsContent">
            @if (filteredPastRuns().length === 0) {
              <div class="empty-runs">
                <div class="empty-runs-icon">📁</div>
                <p>No previous rule runs found for this health plan.</p>
              </div>
            } @else {
              <table class="runs-table">
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Started</th>
                    <th>Rules</th>
                  </tr>
                </thead>
                <tbody>
                  @for (run of filteredPastRuns(); track run.runId) {
                    <tr>
                      <td><strong>{{ run.runId }}</strong></td>
                      <td>{{ run.started }}</td>
                      <td>{{ run.rules }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            }
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    /* Modern CSS with Angular 20+ optimizations */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --primary-blue: #0f62fe;
      --success-green: #198038;
      --warning-yellow: #f1c21b;
      --error-red: #da1e28;
      --background-gray: #f4f4f4;
      --text-primary: #161616;
      --text-muted: #6f6f6f;
      --card-glass: rgba(255, 255, 255, 0.6);
      --space-unit: 8px;
    }

    .container {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--background-gray);
      color: var(--text-primary);
      line-height: 1.5;
      font-weight: 400;
      max-width: 1200px;
      margin: 0 auto;
      padding: calc(var(--space-unit) * 4);
    }

    /* Connection Status Styles */
    .connection-status {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 14px;
      margin-bottom: calc(var(--space-unit) * 2);
      transition: all 200ms ease;
    }

    .status-connected {
      background: #f0fdf4;
      color: var(--success-green);
      border: 1px solid #bbf7d0;
    }

    .status-error {
      background: #fef2f2;
      color: var(--error-red);
      border: 1px solid #fecaca;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    .status-icon {
      font-size: 12px;
    }

    /* Enhanced Progress Tracker */
    .run-metadata {
      background: rgba(15, 98, 254, 0.05);
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 16px;
      font-size: 13px;
    }

    .run-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }

    .progress-percent {
      color: var(--primary-blue);
      font-weight: 600;
    }

    .ai-engine {
      color: var(--text-muted);
    }

    .step-progress {
      margin-left: auto;
      font-size: 12px;
      color: var(--primary-blue);
      font-weight: 500;
    }

    .progress-step.error {
      border-left-color: var(--error-red);
      color: var(--error-red);
      background: rgba(218, 30, 40, 0.05);
    }

    .error-message {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 6px;
      color: var(--error-red);
      font-size: 14px;
      margin-top: 16px;
    }

    .error-icon {
      font-size: 16px;
    }

    .retry-btn {
      background: var(--error-red);
      color: white;
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      margin-left: auto;
      transition: background 200ms ease;
    }

    .retry-btn:hover {
      background: #b91c1c;
    }

    /* Core UI Components */
    header {
      margin-bottom: calc(var(--space-unit) * 4);
    }

    h1 {
      font-size: 32px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: calc(var(--space-unit) * 1);
    }

    .subtitle {
      font-size: 16px;
      color: var(--text-muted);
      font-weight: 400;
    }

    .program-select {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: calc(var(--space-unit) * 3);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .form-group {
      margin-bottom: calc(var(--space-unit) * 2);
    }

    label {
      display: block;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: calc(var(--space-unit) * 1);
    }

    .dropdown {
      width: 100%;
      padding: 10px 16px;
      border-radius: 6px;
      font-size: 14px;
      font-family: 'Inter', sans-serif;
      border: 1px solid #e0e0e0;
      background: white;
      color: var(--text-primary);
      cursor: pointer;
      transition: border-color 200ms ease;
    }

    .dropdown:focus {
      outline: none;
      border-color: var(--primary-blue);
      box-shadow: 0 0 0 3px rgba(15, 98, 254, 0.1);
    }

    .dropdown:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .view-history-btn {
      background: white;
      color: var(--primary-blue);
      border: 1px solid var(--primary-blue);
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 200ms ease;
      margin-top: calc(var(--space-unit) * 2);
    }

    .view-history-btn:hover:not(:disabled) {
      background: var(--primary-blue);
      color: white;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(15, 98, 254, 0.2);
    }

    .view-history-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .empty-state {
      background: #fefce8;
      border: 1px dashed #facc15;
      padding: 16px;
      border-radius: 8px;
      font-style: italic;
      color: #78716c;
      margin-bottom: calc(var(--space-unit) * 3);
      display: none;
    }

    .empty-state.visible {
      display: block;
    }

    .run-btn {
      background: var(--primary-blue);
      color: white;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      transition: all 200ms ease;
      box-shadow: 0 4px 12px rgba(15, 98, 254, 0.2);
      width: 100%;
      margin-bottom: calc(var(--space-unit) * 3);
    }

    .run-btn:hover:not(:disabled) {
      background: #0353e9;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(15, 98, 254, 0.3);
    }

    .run-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      box-shadow: none;
    }

    .progress-tracker {
      display: none;
      flex-direction: column;
      gap: 10px;
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .progress-tracker.visible {
      display: flex;
    }

    .progress-step {
      font-size: 14px;
      padding: 12px 16px;
      border-left: 4px solid #e2e8f0;
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 300ms ease;
    }

    .progress-step.complete {
      border-left-color: var(--success-green);
      color: var(--success-green);
    }

    .progress-step.active {
      border-left-color: var(--primary-blue);
      color: var(--primary-blue);
      background: rgba(15, 98, 254, 0.05);
    }

    .progress-step.pending {
      opacity: 0.5;
    }

    .progress-icon {
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(15, 98, 254, 0.2);
      border-top-color: var(--primary-blue);
      border-radius: 50%;
      animation: spin 800ms linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Modal styles */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      z-index: 999;
      animation: fadeIn 200ms ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .modal {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 90%;
      max-width: 800px;
      max-height: 80vh;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
      animation: slideIn 300ms ease;
      z-index: 1000;
    }

    @keyframes slideIn {
      from {
        transform: translate(-50%, -45%);
        opacity: 0;
      }
      to {
        transform: translate(-50%, -50%);
        opacity: 1;
      }
    }

    .modal-header {
      padding: 24px;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-title {
      font-size: 20px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .modal-close {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: var(--text-muted);
      transition: color 150ms ease;
    }

    .modal-close:hover {
      color: var(--text-primary);
    }

    .modal-body {
      padding: 24px;
      overflow-y: auto;
      max-height: calc(80vh - 160px);
    }

    .modal-search {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
    }

    .search-input {
      flex: 1;
      padding: 10px 16px;
      border-radius: 6px;
      border: 1px solid #e0e0e0;
      font-size: 14px;
      font-family: 'Inter', sans-serif;
    }

    .export-link {
      color: var(--primary-blue);
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .export-link:hover {
      text-decoration: underline;
    }

    .runs-table {
      width: 100%;
      border-collapse: collapse;
    }

    .runs-table th {
      text-align: left;
      padding: 12px;
      font-weight: 600;
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 2px solid #e0e0e0;
    }

    .runs-table td {
      padding: 12px;
      border-bottom: 1px solid #f0f0f0;
    }

    .runs-table tr:hover {
      background: #f9f9f9;
    }

    .empty-runs {
      text-align: center;
      padding: 48px;
      color: var(--text-muted);
    }

    .empty-runs-icon {
      font-size: 48px;
      margin-bottom: 16px;
      opacity: 0.3;
    }

    /* Responsive design */
    @media (max-width: 768px) {
      .container {
        padding: calc(var(--space-unit) * 2);
      }
      
      h1 {
        font-size: 24px;
      }
      
      .modal {
        width: 95%;
        max-height: 90vh;
      }
    }

    /* Angular 20+ specific optimizations */
    @layer base, components, utilities;
    
    /* Performance optimizations for change detection */
    .progress-step {
      contain: layout style;
    }
    
    .modal {
      contain: layout style paint;
    }
  `]
})
export class RuleLandingComponent {
  private router = inject(Router);
  private ruleRunService = inject(RuleRunService);
  private destroyRef = inject(DestroyRef);

  // Form Controls (Angular 20+ Reactive Forms)
  programControl = new FormControl('');
  searchControl = new FormControl('');

  // Signals for reactive state management
  triggerStatus = signal<TriggerStatus | null>(null);
  isRunning = signal(false);
  showModal = signal(false);
  
  // SSE-related signals
  currentRunId = signal<string>('');
  currentProgress = signal<number | null>(null);
  currentAiEngine = signal<string>('');
  connectionStatus = signal<'connected' | 'disconnected' | 'error'>('disconnected');
  hasError = signal(false);
  errorMessage = signal('');
  
  // Static configuration
  programs = signal([
    { value: 'edps-institutional', label: 'EDPS – Institutional' },
    { value: 'edps-professional', label: 'EDPS – Professional' },
    { value: 'medicare-advantage', label: 'Medicare Advantage' },
    { value: 'medicaid-managed', label: 'Medicaid Managed Care' }
  ]);

  progressSteps = signal<ProgressStep[]>([
    { step: 1, name: 'Checking CMS sources', status: 'pending', icon: '' },
    { step: 2, name: 'DeepSeek model running', status: 'pending', icon: '' },
    { step: 3, name: 'Mistral fallback', status: 'pending', icon: '' },
    { step: 4, name: 'Heuristic fallback', status: 'pending', icon: '' },
    { step: 5, name: 'Manual stub detection', status: 'pending', icon: '' },
    { step: 6, name: 'Rule compilation', status: 'pending', icon: '' },
    { step: 7, name: 'Draft ready for review', status: 'pending', icon: '' }
  ]);

  // Mock past runs data
  private mockPastRuns = signal<Record<string, PastRun[]>>({
    'edps-institutional': [
      { runId: 'rr-20250615-002', started: 'June 15, 2025 – 2:30 PM', rules: 12 },
      { runId: 'rr-20250610-001', started: 'June 10, 2025 – 10:15 AM', rules: 10 },
      { runId: 'rr-20250605-003', started: 'June 5, 2025 – 4:45 PM', rules: 11 }
    ],
    'edps-professional': [
      { runId: 'rr-20250618-001', started: 'June 18, 2025 – 11:00 AM', rules: 8 }
    ],
    'medicare-advantage': [],
    'medicaid-managed': []
  });

  // Computed values with Angular 20+ optimizations
  selectedProgram = computed(() => this.programControl.value || '');
  searchTerm = computed(() => this.searchControl.value || '');

  currentPastRuns = computed(() => {
    return this.mockPastRuns()[this.selectedProgram()] || [];
  });

  filteredPastRuns = computed(() => {
    const runs = this.currentPastRuns();
    const term = this.searchTerm().toLowerCase();
    if (!term) return runs;
    return runs.filter(run => 
      run.runId.toLowerCase().includes(term) || 
      run.started.toLowerCase().includes(term)
    );
  });

  showEmptyState = computed(() => {
    const program = this.selectedProgram();
    return program && this.currentPastRuns().length === 0;
  });

  emptyStateMessage = computed(() => {
    return 'No previous rule runs found for this program. CMS source files have been updated since last run.';
  });

  canRunRule = computed(() => {
    return this.selectedProgram() && !this.isRunning();
  });

  getRunButtonText = computed(() => {
    if (!this.isRunning()) return 'Run Health Plan Rule Run';
    if (this.connectionStatus() === 'error') return 'Connection Error - Retrying...';
    if (this.currentProgress() !== null) {
      return `Running... ${this.currentProgress()?.toFixed(0)}%`;
    }
    return 'Running...';
  });

  constructor() {
    // Load saved program on init
    effect(() => {
      const savedProgram = sessionStorage.getItem('selectedProgram');
      if (savedProgram) {
        this.programControl.setValue(savedProgram);
      }
    });

    // React to program changes
    effect(() => {
      const program = this.selectedProgram();
      if (program) {
        sessionStorage.setItem('selectedProgram', program);
        this.checkTriggerEligibility();
      }
    });

    // Subscribe to SSE progress updates using takeUntilDestroyed
    this.ruleRunService.progressUpdates$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((progress: ProgressEvent) => {
        this.handleProgressUpdate(progress);
      });

    // Subscribe to connection status using takeUntilDestroyed
    this.ruleRunService.connectionStatus$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.connectionStatus.set(status);
        
        if (status === 'error') {
          this.hasError.set(true);
          this.errorMessage.set('Lost connection to server. Attempting to reconnect...');
        } else if (status === 'connected') {
          this.hasError.set(false);
          this.errorMessage.set('');
        }
      });
  }

  private checkTriggerEligibility() {
    this.ruleRunService.checkTriggerEligibility().subscribe({
      next: (status) => {
        this.triggerStatus.set(status);
      },
      error: (error) => {
        console.error('Failed to check trigger eligibility:', error);
      }
    });
  }

  startRuleRun() {
    if (!this.canRunRule()) return;

    this.isRunning.set(true);
    this.hasError.set(false);
    this.resetProgress();
    
    // Use enhanced service method that automatically connects to SSE
    this.ruleRunService.triggerRuleRunWithProgress(this.selectedProgram()).subscribe({
      next: (response) => {
        console.log('Rule run started:', response);
        this.currentRunId.set(response.runId);
        
        // Store run metadata
        const timestamp = new Date().toLocaleString('en-US', { 
          month: 'long', 
          day: 'numeric', 
          year: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          hour12: true 
        });
        
        sessionStorage.setItem('currentRunId', response.runId);
        sessionStorage.setItem('runStarted', timestamp);
      },
      error: (error) => {
        console.error('Failed to start rule run:', error);
        this.isRunning.set(false);
        this.hasError.set(true);
        this.errorMessage.set('Failed to start rule extraction. Please try again.');
        this.resetProgress();
      }
    });
  }

  private handleProgressUpdate(progress: ProgressEvent) {
    console.log('Handling progress update:', progress);
    
    // Update progress tracking
    this.currentProgress.set(progress.progress);
    this.currentAiEngine.set(progress.aiEngine || '');
    
    // Update progress steps based on currentStep
    this.updateProgressStep(progress.currentStep, progress.stepName, progress.status);
    
    // Handle completion
    if (progress.status === 'completed') {
      this.isRunning.set(false);
      setTimeout(() => {
        this.router.navigate(['/admin/rule-review']);
      }, 1000);
    } else if (progress.status === 'failed') {
      this.isRunning.set(false);
      this.hasError.set(true);
      this.errorMessage.set('Rule extraction failed. Please check the logs and try again.');
    }
  }

  private updateProgressStep(currentStep: number, stepName: string, status: string) {
    const steps = this.progressSteps();
    
    // Reset all steps based on current progress
    steps.forEach(step => {
      if (step.step < currentStep) {
        step.status = 'complete';
        step.icon = '✓';
      } else if (step.step === currentStep) {
        step.status = status === 'failed' ? 'error' : 'active';
        step.icon = status === 'failed' ? '❌' : '<div class="spinner"></div>';
      } else {
        step.status = 'pending';
        step.icon = '';
      }
    });
    
    // Update the current step name to match backend
    if (currentStep > 0 && currentStep <= steps.length) {
      steps[currentStep - 1].name = stepName;
    }
    
    this.progressSteps.set([...steps]);
  }

  private resetProgress() {
    const steps = this.progressSteps().map(step => ({
      ...step,
      status: 'pending' as const,
      icon: ''
    }));
    this.progressSteps.set(steps);
    this.currentProgress.set(null);
    this.currentAiEngine.set('');
  }

  retryConnection() {
    const runId = this.currentRunId();
    if (runId) {
      this.hasError.set(false);
      this.ruleRunService.connectToProgressStream(runId);
    }
  }

  // Modal methods
  openPastRunsModal() {
    if (!this.selectedProgram()) {
      alert('Please select a program first');
      return;
    }
    this.showModal.set(true);
  }

  closePastRunsModal() {
    this.showModal.set(false);
    this.searchControl.setValue('');
  }
}
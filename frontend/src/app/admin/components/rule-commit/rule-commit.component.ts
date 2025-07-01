// frontend/src/app/admin/components/rule-commit/rule-commit.component.ts

import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { RuleRunService } from '../../services/rule-run.service';
import { CommitResponse } from '../../../shared/models/rule.models';

@Component({
  selector: 'app-rule-commit',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container">
      <header>
        <h1>Review Summary & Commit</h1>
        <p class="subtitle">Confirm rule selections before finalizing the commit</p>
      </header>

      <div class="summary-metadata">
        <div class="metadata-grid">
          <div class="metadata-item">
            <span class="metadata-label">Program</span>
            <span class="metadata-value">{{ programName() }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Run ID</span>
            <span class="metadata-value">{{ runId() }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Started</span>
            <span class="metadata-value">{{ startTime() }}</span>
          </div>
        </div>
      </div>

      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-icon approved">✓</div>
          <div class="card-content">
            <div class="card-number">{{ approvedCount() }}</div>
            <div class="card-label">Rules Approved</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="card-icon rejected">✗</div>
          <div class="card-content">
            <div class="card-number">{{ rejectedCount() }}</div>
            <div class="card-label">Rules Rejected</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="card-icon manual">⚠️</div>
          <div class="card-content">
            <div class="card-number">{{ manualCount() }}</div>
            <div class="card-label">Manual Stubs Required</div>
          </div>
        </div>
      </div>

      @if (tags().length > 0) {
        <div class="tag-summary">
          @for (tag of tags(); track tag) {
            <span class="badge" [class]="getBadgeClass(tag)">{{ formatTag(tag) }}</span>
          }
        </div>
      }

      <div class="disabled-rules">
        <div class="disabled-rules-title">Disabled Rules (Not Included)</div>
        <div class="disabled-rules-list">{{ disabledRules().join(', ') }}</div>
      </div>

      <div class="status-confirmation">
        <span class="status-icon">✓</span>
        <span>Ready to Commit</span>
      </div>

      <div class="actions">
        <button 
          class="btn-primary" 
          [disabled]="isCommitting()"
          (click)="finalizeCommit()">
          {{ isCommitting() ? 'Committing...' : 'Finalize Rule Commit' }}
        </button>
        <button 
          class="btn-secondary" 
          [disabled]="isCommitting()"
          (click)="backToReview()">
          Back to Review
        </button>
      </div>

      @if (commitResponse()) {
        <div class="commit-success">
          <div class="success-message">
            <span class="success-icon">✓</span>
            <span>{{ commitResponse()?.message }}</span>
          </div>
          
          @if (commitResponse()?.generatedFiles) {
            <div class="generated-files">
              <h4>Generated Files:</h4>
              <ul>
                @for (file of getGeneratedFilesList(); track file) {
                  <li>{{ file }}</li>
                }
              </ul>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    /* Copy exact styles from rule-commit.html */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --primary-blue: #0f62fe;
      --success-green: #22c55e;
      --warning-yellow: #facc15;
      --error-red: #ef4444;
      --background-gray: #f4f4f4;
      --text-primary: #161616;
      --text-muted: #6f6f6f;
      --card-glass: rgba(255, 255, 255, 0.6);
      --space-unit: 8px;
    }

    body, .container {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--background-gray);
      color: var(--text-primary);
      line-height: 1.5;
      font-weight: 400;
    }

    .container {
      max-width: 1024px;
      margin: 0 auto;
      padding: 24px;
    }

    header {
      margin-bottom: calc(var(--space-unit) * 4);
    }

    h1 {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: calc(var(--space-unit) * 1);
    }

    .subtitle {
      font-size: 16px;
      color: var(--text-muted);
      font-weight: 400;
    }

    .summary-metadata {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: calc(var(--space-unit) * 3);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .metadata-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: calc(var(--space-unit) * 2);
    }

    .metadata-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .metadata-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .metadata-value {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: calc(var(--space-unit) * 2);
      margin-bottom: calc(var(--space-unit) * 3);
    }

    .summary-card {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .card-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: 700;
    }

    .card-icon.approved {
      background: rgba(34, 197, 94, 0.1);
      color: var(--success-green);
    }

    .card-icon.rejected {
      background: rgba(239, 68, 68, 0.1);
      color: var(--error-red);
    }

    .card-icon.manual {
      background: rgba(250, 204, 21, 0.1);
      color: #ca8a04;
    }

    .card-content {
      flex: 1;
    }

    .card-number {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 4px;
    }

    .card-label {
      font-size: 14px;
      color: var(--text-muted);
      font-weight: 600;
    }

    .tag-summary {
      text-align: center;
      margin-bottom: 24px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      margin-right: 8px;
    }

    .badge.high-risk {
      background-color: rgba(239, 68, 68, 0.1);
      color: var(--error-red);
    }

    .badge.manual-stub {
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      color: #92400e;
    }

    .badge.fallback {
      background-color: rgba(15, 98, 254, 0.1);
      color: var(--primary-blue);
    }

    .disabled-rules {
      background: #f9f9f9;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: calc(var(--space-unit) * 4);
    }

    .disabled-rules-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .disabled-rules-list {
      font-family: 'Monaco', 'Menlo', monospace;
      font-size: 14px;
      color: var(--text-primary);
      line-height: 1.6;
    }

    .actions {
      display: flex;
      gap: calc(var(--space-unit) * 2);
      justify-content: center;
      margin-bottom: calc(var(--space-unit) * 3);
    }

    .btn-primary {
      background: var(--primary-blue);
      color: white;
      padding: 16px 32px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      transition: all 200ms ease;
      box-shadow: 0 4px 12px rgba(15, 98, 254, 0.2);
    }

    .btn-primary:hover:not(:disabled) {
      background: #0353e9;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(15, 98, 254, 0.3);
    }

    .btn-primary:disabled {
      background: #cbd5e0;
      cursor: not-allowed;
      box-shadow: none;
    }

    .btn-secondary {
      background: white;
      color: var(--text-primary);
      padding: 16px 32px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      border: 2px solid #e0e0e0;
      cursor: pointer;
      transition: all 200ms ease;
    }

    .btn-secondary:hover:not(:disabled) {
      border-color: var(--text-primary);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .status-confirmation {
      text-align: center;
      color: var(--success-green);
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-bottom: calc(var(--space-unit) * 2);
    }

    .status-icon {
      font-size: 20px;
    }

    .commit-success {
      background: #f0fdf4;
      border: 1px solid #22c55e;
      border-radius: 12px;
      padding: 24px;
    }

    .success-message {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }

    .success-icon {
      color: #22c55e;
      font-size: 24px;
    }

    .generated-files h4 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 8px;
      color: #065f46;
    }

    .generated-files ul {
      list-style: none;
      padding: 0;
    }

    .generated-files li {
      background: rgba(34, 197, 94, 0.1);
      padding: 4px 8px;
      border-radius: 4px;
      margin-bottom: 4px;
      font-family: monospace;
      font-size: 12px;
    }

    @media (max-width: 768px) {
      .summary-cards {
        grid-template-columns: 1fr;
      }
      
      .actions {
        flex-direction: column;
      }
      
      .btn-primary, .btn-secondary {
        width: 100%;
      }
    }
  `]
})
export class RuleCommitComponent implements OnInit {
  private router = inject(Router);
  private ruleRunService = inject(RuleRunService);

  // Signals
  isCommitting = signal(false);
  commitResponse = signal<CommitResponse | null>(null);

  // Computed values
  programMap = computed(() => ({
    'edps-institutional': 'EDPS – Institutional',
    'edps-professional': 'EDPS – Professional',
    'medicare-advantage': 'Medicare Advantage',
    'medicaid-managed': 'Medicaid Managed Care'
  }));

  programName = computed(() => {
    const program = sessionStorage.getItem('selectedProgram') || '';
    const map = this.programMap();
    return map[program as keyof typeof map] || 'Unknown Program';
  });

  runId = computed(() => {
    return sessionStorage.getItem('currentRunId') || 'rr-20250621-001';
  });

  startTime = computed(() => {
    return sessionStorage.getItem('runStarted') || 'June 21, 2025 – 12:43 PM';
  });

  decisions = computed(() => {
    return JSON.parse(sessionStorage.getItem('ruleDecisions') || '{}');
  });

  approvedCount = computed(() => {
    return Object.values(this.decisions()).filter((d: any) => d.status === 'approved').length;
  });

  rejectedCount = computed(() => {
    return Object.values(this.decisions()).filter((d: any) => d.status === 'rejected').length;
  });

  manualCount = computed(() => {
    return Object.values(this.decisions()).filter((d: any) => 
      d.tags && d.tags.includes('manual_stub')
    ).length;
  });

  tags = computed(() => {
    const allTags = new Set<string>();
    Object.values(this.decisions()).forEach((decision: any) => {
      if (decision.tags) {
        decision.tags.forEach((tag: string) => allTags.add(tag));
      }
    });
    return Array.from(allTags);
  });

  disabledRules = signal(['TRC203', 'TRC204', 'TRC219']);

  ngOnInit() {
    // Component initialization logic
  }

  getBadgeClass(tag: string): string {
    if (tag === 'high-risk') return 'high-risk';
    if (tag === 'manual_stub') return 'manual-stub';
    return 'fallback';
  }

  formatTag(tag: string): string {
    return tag.replace('_', ' ');
  }

  getGeneratedFilesList(): string[] {
    const response = this.commitResponse();
    if (!response?.generatedFiles) return [];
    return Object.values(response.generatedFiles);
  }

  finalizeCommit() {
    this.isCommitting.set(true);
    
    this.ruleRunService.commitRules(this.programName()).subscribe({
      next: (response) => {
        this.commitResponse.set(response);
        this.isCommitting.set(false);
        this.showToast('Rule Run Committed Successfully');
        
        // Navigate to past runs after delay
        setTimeout(() => {
          sessionStorage.clear();
          this.router.navigate(['/admin/rule-landing']);
        }, 3000);
      },
      error: (error) => {
        console.error('Failed to commit rules:', error);
        this.isCommitting.set(false);
      }
    });
  }

  backToReview() {
    this.router.navigate(['/admin/rule-review']);
  }

  private showToast(message: string) {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
      background: #22c55e;
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
      z-index: 2000;
      animation: fadeInUp 400ms ease-in-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }
}
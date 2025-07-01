// frontend/src/app/admin/components/rule-review/rule-review.component.ts

import { Component, signal, computed, effect, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { RuleRunService } from '../../services/rule-run.service';
import { RuleModel } from '../../../shared/models/rule.models';

interface RuleWithDecision extends RuleModel {
  decision?: 'approved' | 'rejected' | null;
}

@Component({
  selector: 'app-rule-review',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">Program Rule Setup</h1>
        <div class="metadata-grid">
          <div class="metadata-item">
            <span class="metadata-label">Program</span>
            <span class="metadata-value">{{ programDisplay() }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Run ID</span>
            <span class="metadata-value">{{ runIdDisplay() }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Started</span>
            <span class="metadata-value">{{ startTimeDisplay() }}</span>
          </div>
        </div>
      </div>

      <!-- Confidence Score Chart -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">Confidence Score Overview</h2>
          <p class="chart-subtitle">Click on a bar to jump to that rule</p>
        </div>
        <div class="chart-wrapper">
          <canvas #confidenceChart></canvas>
        </div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Rule ID</th>
              <th>Description</th>
              <th>Confidence</th>
              <th>Engine</th>
              <th>Tags</th>
              <th>Actions</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            @for (rule of rules(); track rule.id) {
              <tr 
                [class.has-decision]="rule.decision !== null"
                [class.approved]="rule.decision === 'approved'"
                [class.rejected]="rule.decision === 'rejected'">
                <td class="rule-id">{{ rule.id }}</td>
                <td class="description">{{ rule.description }}</td>
                <td>
                  <span class="badge confidence-badge"
                        [class.confidence-high]="rule.confidence >= 85"
                        [class.confidence-medium]="rule.confidence >= 70 && rule.confidence < 85"
                        [class.confidence-low]="rule.confidence < 70">
                    {{ rule.confidence }}%
                  </span>
                </td>
                <td>
                  <span class="badge engine-badge"
                        [class.heuristic]="rule.engine === 'Heuristic'">
                    {{ rule.engine }}
                  </span>
                </td>
                <td>
                  @for (tag of rule.tags || []; track tag) {
                    <span class="badge tag"
                          [class.high-risk]="tag === 'high-risk'"
                          [class.manual-stub]="tag === 'manual_stub'">
                      {{ tag === 'manual_stub' ? 'manual stub' : tag }}
                    </span>
                  }
                </td>
                <td class="actions">
                  <button 
                    class="btn btn-approve"
                    [class.active]="rule.decision === 'approved'"
                    (click)="toggleAction(rule.id, 'approve')"
                    [attr.aria-pressed]="rule.decision === 'approved'">
                    {{ rule.decision === 'approved' ? 'Approved' : 'Approve' }}
                  </button>
                  <button 
                    class="btn btn-reject"
                    [class.active]="rule.decision === 'rejected'"
                    (click)="toggleAction(rule.id, 'reject')"
                    [attr.aria-pressed]="rule.decision === 'rejected'">
                    {{ rule.decision === 'rejected' ? 'Rejected' : 'Reject' }}
                  </button>
                </td>
                <td>
                  <span class="arrow-icon" (click)="openDrawer(rule.id)">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"/>
                    </svg>
                  </span>
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>

      <div class="footer-container">
        <button 
          class="btn-primary"
          [class.loading]="isSubmitting()"
          [disabled]="!canSubmit() || isSubmitting()"
          (click)="submitRuleRun()">
          {{ isSubmitting() ? '' : 'Accept Rule Run' }}
        </button>
      </div>
    </div>

    @if (showDrawer()) {
      <div class="overlay" (click)="closeDrawer()"></div>
      <div class="drawer open">
        <div class="drawer-header">
          <h2 class="drawer-title">Rule Details</h2>
          <button class="close-btn" (click)="closeDrawer()">&times;</button>
        </div>
        <div [innerHTML]="drawerContent()"></div>
      </div>
    }
  `,
  styles: [`
    /* Copy exact styles from rule-review.html */
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

    body, .container {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--background-gray);
      color: var(--text-primary);
      line-height: 1.5;
      font-weight: 400;
    }

    .container {
      max-width: 1440px;
      margin: 0 auto;
      padding: calc(var(--space-unit) * 4);
    }

    .page-header {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: calc(var(--space-unit) * 4);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .page-title {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: calc(var(--space-unit) * 2);
    }

    .metadata-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: calc(var(--space-unit) * 2);
    }

    .metadata-item {
      display: flex;
      flex-direction: column;
      gap: calc(var(--space-unit) * 0.5);
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

    .chart-container {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: calc(var(--space-unit) * 3);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .chart-header {
      margin-bottom: calc(var(--space-unit) * 2);
    }

    .chart-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .chart-subtitle {
      font-size: 14px;
      color: var(--text-muted);
    }

    .chart-wrapper {
      position: relative;
      height: 200px;
    }

    .table-container {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.8);
      overflow: hidden;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    thead {
      background-color: rgba(244, 244, 244, 0.8);
      border-bottom: 1px solid rgba(22, 22, 22, 0.1);
    }

    th {
      padding: calc(var(--space-unit) * 2);
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    td {
      padding: calc(var(--space-unit) * 2);
      border-bottom: 1px solid rgba(22, 22, 22, 0.05);
      font-weight: 400;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover {
      background-color: rgba(15, 98, 254, 0.02);
    }

    tr.has-decision {
      background-color: rgba(15, 98, 254, 0.03);
      border-left: 3px solid transparent;
    }

    tr.has-decision.approved {
      border-left-color: #22c55e;
      background-color: rgba(34, 197, 94, 0.03);
    }

    tr.has-decision.rejected {
      border-left-color: #ef4444;
      background-color: rgba(239, 68, 68, 0.03);
    }

    .rule-id {
      font-weight: 700;
      color: var(--text-primary);
    }

    .description {
      color: var(--text-primary);
      max-width: 400px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }

    .confidence-badge {
      font-weight: 600;
    }

    .confidence-high {
      background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
      color: var(--success-green);
    }

    .confidence-medium {
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      color: #92400e;
    }

    .confidence-low {
      background-color: #fee2e2;
      color: var(--error-red);
    }

    .engine-badge {
      background-color: rgba(15, 98, 254, 0.1);
      color: var(--primary-blue);
    }

    .engine-badge.heuristic {
      background: linear-gradient(135deg, #d1fae5 0%, #bbf7d0 100%);
      color: var(--success-green);
    }

    .tag {
      background-color: rgba(111, 111, 111, 0.1);
      color: var(--text-muted);
      margin-right: calc(var(--space-unit) * 0.5);
    }

    .tag.high-risk {
      background-color: rgba(218, 30, 40, 0.1);
      color: var(--error-red);
    }

    .tag.manual-stub {
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      color: #92400e;
    }

    .tag.manual-stub::before {
      content: '⚠️';
      margin-right: 4px;
    }

    .actions {
      display: flex;
      gap: var(--space-unit);
    }

    .btn {
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      transition: all 200ms ease-in-out;
      font-family: 'Inter', sans-serif;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .btn-approve {
      background-color: #d1fae5;
      color: #065f46;
      border: 1px solid transparent;
    }

    .btn-approve:hover:not(.active) {
      background-color: #a7f3d0;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(6, 95, 70, 0.15);
    }

    .btn-reject {
      background-color: #fee2e2;
      color: #991b1b;
      border: 1px solid transparent;
    }

    .btn-reject:hover:not(.active) {
      background-color: #fecaca;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(153, 27, 27, 0.15);
    }

    .btn-approve.active {
      background-color: #22c55e;
      color: white;
    }

    .btn-approve.active::before {
      content: '✓';
      font-size: 16px;
      font-weight: 700;
    }

    .btn-reject.active {
      background-color: #ef4444;
      color: white;
    }

    .btn-reject.active::before {
      content: '✗';
      font-size: 16px;
      font-weight: 700;
    }

    .arrow-icon {
      color: #cbd5e0;
      cursor: pointer;
      transition: all 150ms ease-in;
    }

    .arrow-icon:hover {
      color: var(--primary-blue);
      transform: translateX(2px);
    }

    .footer-container {
      margin-top: calc(var(--space-unit) * 4);
      display: flex;
      justify-content: center;
    }

    .btn-primary {
      background-color: var(--primary-blue);
      color: white;
      padding: 12px 32px;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 700;
      border: none;
      cursor: pointer;
      transition: all 200ms ease-in-out;
      box-shadow: 0 4px 12px rgba(15, 98, 254, 0.2);
      position: relative;
      overflow: hidden;
    }

    .btn-primary:hover:not(:disabled) {
      background-color: #0353e9;
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(15, 98, 254, 0.3);
    }

    .btn-primary:disabled {
      background-color: rgba(111, 111, 111, 0.3);
      cursor: not-allowed;
      box-shadow: none;
    }

    .btn-primary.loading::after {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      top: 50%;
      left: 50%;
      margin-left: -10px;
      margin-top: -10px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spinner 600ms linear infinite;
    }

    @keyframes spinner {
      to { transform: rotate(360deg); }
    }

    .drawer {
      position: fixed;
      top: 0;
      right: -480px;
      width: 480px;
      height: 100vh;
      background: var(--card-glass);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
      transition: right 400ms ease-in-out;
      z-index: 1000;
      padding: 24px;
      overflow-y: auto;
    }

    .drawer.open {
      right: 0;
    }

    .drawer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: calc(var(--space-unit) * 3);
    }

    .drawer-title {
      font-size: 20px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: var(--text-muted);
      transition: color 150ms ease-in;
    }

    .close-btn:hover {
      color: var(--text-primary);
    }

    .overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      z-index: 999;
      transition: opacity 400ms ease-in-out;
    }

    @media (max-width: 1024px) {
      .container {
        padding: calc(var(--space-unit) * 2);
      }
      
      .metadata-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 768px) {
      .drawer {
        width: 100%;
        right: -100%;
      }
      
      .description {
        max-width: 200px;
      }
    }
  `]
})
export class RuleReviewComponent implements OnInit {
  private router = inject(Router);
  private ruleRunService = inject(RuleRunService);

  // Signals
  rules = signal<RuleWithDecision[]>([]);
  isSubmitting = signal(false);
  showDrawer = signal(false);
  selectedRuleId = signal<string | null>(null);
  
  // Computed values
  programDisplay = computed(() => {
    const programMap: Record<string, string> = {
      'edps-institutional': 'EDPS – Institutional',
      'edps-professional': 'EDPS – Professional',
      'medicare-advantage': 'Medicare Advantage',
      'medicaid-managed': 'Medicaid Managed Care'
    };
    const program = sessionStorage.getItem('selectedProgram') || '';
    return programMap[program] || 'Unknown Program';
  });

  runIdDisplay = computed(() => {
    return sessionStorage.getItem('currentRunId') || 'rr-20250621-001';
  });

  startTimeDisplay = computed(() => {
    return sessionStorage.getItem('runStarted') || 'June 21, 2025 – 12:43 PM';
  });

  canSubmit = computed(() => {
    return this.rules().every(rule => rule.decision !== null);
  });

  drawerContent = computed(() => {
    const ruleId = this.selectedRuleId();
    if (!ruleId) return '';
    
    return `
      <div class="drawer-section">
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">🔖</span>
            Rule ID
          </h3>
          <p style="color: #161616; font-weight: 600;">${ruleId}</p>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">📝</span>
            Full Description
          </h3>
          <p style="color: #161616; line-height: 1.6;">This rule validates that all patient admission dates fall within the current reporting period. The validation ensures compliance with CMS reporting requirements and prevents data quality issues.</p>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">📄</span>
            Source Document
          </h3>
          <p style="color: #161616;">CMS-1500 Form Instructions v2024.3</p>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">🤖</span>
            Engine
          </h3>
          <span class="badge engine-badge">DeepSeek</span>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">⚠️</span>
            Tags
          </h3>
          <div style="display: flex; gap: 8px;">
            <span class="badge tag high-risk">high-risk</span>
            <span class="badge tag manual-stub">manual_stub</span>
          </div>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">📋</span>
            Extracted Text
          </h3>
          <div style="background: rgba(244, 244, 244, 0.8); padding: 16px; border-radius: 8px; font-family: 'Inter', monospace; font-size: 14px; color: #161616; border: 1px solid rgba(22, 22, 22, 0.1);">
            "The admission date must be within the reporting period dates specified in the header record..."
          </div>
        </div>
        <div class="drawer-item">
          <h3 class="drawer-label">
            <span class="drawer-icon">💻</span>
            Rule Logic
          </h3>
          <pre style="background: #161616; color: #f4f4f4; padding: 16px; border-radius: 8px; font-size: 14px; overflow-x: auto; font-family: 'Monaco', 'Menlo', monospace;">
if (admissionDate < reportingPeriod.start || 
    admissionDate > reportingPeriod.end) {
    return {
        valid: false,
        error: "Admission date outside reporting period"
    };
}</pre>
        </div>
      </div>
    `;
  });

  ngOnInit() {
    this.loadRules();
  }

  private loadRules() {
    // Load mock rules data
    const mockRules: RuleWithDecision[] = [
      {
        id: 'TRC004',
        description: 'Validate patient admission date must be within reporting period',
        engine: 'DeepSeek',
        confidence: 95,
        status: 'pending',
        tags: ['high-risk'],
        decision: null
      },
      {
        id: 'TRC005',
        description: 'Check discharge status code against CMS allowed values',
        engine: 'Mistral',
        confidence: 78,
        status: 'pending',
        tags: ['manual_stub'],
        decision: null
      },
      {
        id: 'TRC006',
        description: 'Ensure DRG code matches patient diagnosis and procedures',
        engine: 'DeepSeek',
        confidence: 92,
        status: 'pending',
        tags: [],
        decision: null
      },
      {
        id: 'TRC007',
        description: 'Verify provider NPI is active and valid',
        engine: 'Heuristic',
        confidence: 65,
        status: 'pending',
        tags: ['manual_stub'],
        decision: null
      },
      {
        id: 'TRC008',
        description: 'Validate Medicare beneficiary ID format and checksum',
        engine: 'Mistral',
        confidence: 88,
        status: 'pending',
        tags: ['high-risk'],
        decision: null
      }
    ];

    this.rules.set(mockRules);
  }

  toggleAction(ruleId: string, action: 'approve' | 'reject') {
    const currentRules = this.rules();
    const updatedRules = currentRules.map(rule => {
      if (rule.id === ruleId) {
        const mappedDecision = action === 'approve' ? 'approved' as const : 'rejected' as const;
        // If clicking the same action, toggle it off
        if (rule.decision === mappedDecision) {
          return { ...rule, decision: null };
        }
        // Otherwise set the new decision
        return { ...rule, decision: mappedDecision };
      }
      return rule;
    });
    
    this.rules.set(updatedRules);
    this.saveDecisions();
  }

  private saveDecisions() {
    const decisions: Record<string, any> = {};
    this.rules().forEach(rule => {
      if (rule.decision) {
        decisions[rule.id] = {
          status: rule.decision,
          tags: rule.tags || []
        };
      }
    });
    sessionStorage.setItem('ruleDecisions', JSON.stringify(decisions));
  }

  submitRuleRun() {
    if (!this.canSubmit()) return;

    this.isSubmitting.set(true);

    // Simulate API call
    setTimeout(() => {
      this.isSubmitting.set(false);
      this.showToast('Rule run accepted successfully');
      
      setTimeout(() => {
        this.router.navigate(['/admin/rule-commit']);
      }, 1500);
    }, 2000);
  }

  private showToast(message: string) {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
      background: #161616;
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 2000;
      animation: fadeInUp 400ms ease-in-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'fadeOutDown 400ms ease-in-out';
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  openDrawer(ruleId: string) {
    this.selectedRuleId.set(ruleId);
    this.showDrawer.set(true);
  }

  closeDrawer() {
    this.showDrawer.set(false);
    this.selectedRuleId.set(null);
  }
}
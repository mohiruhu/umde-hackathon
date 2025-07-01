// frontend/src/app/admin/components/rule-past-runs/rule-past-runs.component.ts

import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { RuleRunService } from '../../services/rule-run.service';
import { RuleRunHistory } from '../../../shared/models/rule.models';

@Component({
  selector: 'app-rule-past-runs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <header class="page-header">
        <h1 class="page-title">Past Rule Runs</h1>
        <div class="header-actions">
          <button class="btn-secondary" (click)="onBackToLanding()">
            Back to Landing
          </button>
        </div>
      </header>

      <section class="filters-section">
        <div class="search-bar">
          <input 
            type="text" 
            placeholder="Search runs..." 
            [(ngModel)]="searchTerm"
            (input)="onSearch()">
        </div>
        <button class="export-btn" (click)="onExport()">Export</button>
      </section>

      @if (filteredRuns().length > 0) {
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Started</th>
                <th>Status</th>
                <th>Rules</th>
                <th>Approved</th>
                <th>Rejected</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              @for (run of filteredRuns(); track run.runId) {
                <tr>
                  <td class="run-id">{{ run.runId }}</td>
                  <td>{{ run.started | date:'medium' }}</td>
                  <td>
                    <span class="badge status-badge"
                          [class.status-completed]="run.status === 'completed'"
                          [class.status-failed]="run.status === 'failed'"
                          [class.status-in-progress]="run.status === 'in-progress'">
                      {{ run.status }}
                    </span>
                  </td>
                  <td>{{ run.rulesCount }}</td>
                  <td class="count approved">{{ run.approvedCount || 0 }}</td>
                  <td class="count rejected">{{ run.rejectedCount || 0 }}</td>
                  <td>
                    <button 
                      class="btn-link"
                      [disabled]="run.status !== 'completed'"
                      (click)="onViewRun(run)">
                      View Details
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      } @else {
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <p>No previous rule runs found for this health plan.</p>
          <button class="btn-primary" (click)="onStartNewRun()">
            Start New Rule Run
          </button>
        </div>
      }
    </div>
  `,
  styles: [`
    /* Copy exact styles from rule-past-runs section in the HTML */
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
      padding: 24px;
    }

    .page-header {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-title {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .filters-section {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      display: flex;
      gap: 16px;
      align-items: center;
    }

    .search-bar {
      flex: 1;
    }

    .search-bar input {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
    }

    .export-btn {
      background: #f3f4f6;
      color: #374151;
      border: 1px solid #d1d5db;
      padding: 12px 24px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }

    .table-container {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th {
      padding: 16px;
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      color: #4a5568;
      text-transform: uppercase;
      background-color: #f7fafc;
    }

    td {
      padding: 16px;
      border-bottom: 1px solid #e2e8f0;
    }

    tr:hover {
      background-color: rgba(15, 98, 254, 0.02);
    }

    .run-id {
      font-weight: 700;
      color: var(--text-primary);
      font-family: monospace;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-completed {
      background: #d1fae5;
      color: #065f46;
    }

    .status-failed {
      background: #fee2e2;
      color: #991b1b;
    }

    .status-in-progress {
      background: #dbeafe;
      color: #1e40af;
    }

    .count {
      font-weight: 700;
      text-align: center;
    }

    .count.approved {
      color: #22c55e;
    }

    .count.rejected {
      color: #ef4444;
    }

    .btn-link {
      background: none;
      color: var(--primary-blue);
      border: none;
      cursor: pointer;
      font-weight: 600;
      text-decoration: underline;
    }

    .btn-link:disabled {
      color: #9ca3af;
      cursor: not-allowed;
      text-decoration: none;
    }

    .btn-secondary {
      background: white;
      color: #374151;
      border: 1px solid #d1d5db;
      padding: 12px 24px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
    }

    .btn-primary {
      background: var(--primary-blue);
      color: white;
      padding: 12px 24px;
      border-radius: 6px;
      border: none;
      font-weight: 600;
      cursor: pointer;
    }

    .empty-state {
      background: var(--card-glass);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 60px;
      text-align: center;
    }

    .empty-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    .empty-state p {
      color: var(--text-muted);
      margin-bottom: 24px;
    }
  `]
})
export class RulePastRunsComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private ruleRunService = inject(RuleRunService);

  // Signals
  program = signal('');
  searchTerm = signal('');
  allRuns = signal<RuleRunHistory[]>([]);

  // Computed
  filteredRuns = computed(() => {
    const runs = this.allRuns();
    const term = this.searchTerm().toLowerCase();
    if (!term) return runs;
    return runs.filter(run =>
      run.runId.toLowerCase().includes(term)
    );
  });

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.program.set(params['program'] || 'edps-institutional');
      this.loadPastRuns();
    });
  }

  onSearch() {
    // Filtering handled by computed signal
  }

  onExport() {
    const csvContent = this.generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rule-runs-${this.program()}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  onViewRun(run: RuleRunHistory) {
    this.router.navigate(['/admin/rule-review'], {
      queryParams: { program: this.program(), runId: run.runId }
    });
  }

  onBackToLanding() {
    this.router.navigate(['/admin/rule-landing']);
  }

  onStartNewRun() {
    this.router.navigate(['/admin/rule-landing'], {
      queryParams: { program: this.program() }
    });
  }

  private loadPastRuns() {
    this.ruleRunService.getPastRuns(this.program()).subscribe({
      next: (runs) => {
        this.allRuns.set(runs);
      },
      error: (error) => {
        console.error('Failed to load past runs:', error);
        // Mock data for testing
        this.allRuns.set(this.getMockRuns());
      }
    });
  }

  private generateCSV(): string {
    const headers = ['Run ID', 'Started', 'Status', 'Rules Count', 'Approved', 'Rejected'];
    const rows = this.filteredRuns().map(run => [
      run.runId,
      run.started.toISOString(),
      run.status,
      run.rulesCount.toString(),
      (run.approvedCount || 0).toString(),
      (run.rejectedCount || 0).toString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  private getMockRuns(): RuleRunHistory[] {
    return [
      {
        runId: 'rr-20250625-001',
        planId: this.program(),
        started: new Date('2025-06-25T10:30:00'),
        completed: new Date('2025-06-25T10:45:00'),
        status: 'completed',
        rulesCount: 5,
        approvedCount: 3,
        rejectedCount: 2
      },
      {
        runId: 'rr-20250624-003',
        planId: this.program(),
        started: new Date('2025-06-24T14:20:00'),
        completed: new Date('2025-06-24T14:35:00'),
        status: 'completed',
        rulesCount: 7,
        approvedCount: 6,
        rejectedCount: 1
      }
    ];
  }
}
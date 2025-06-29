/**
 * Type definitions for Rule Management
 * Location: frontend/src/app/shared/models/rule.models.ts
 */

/**
 * Represents a group of rules from a specific AI engine
 */
export interface RuleRunGroup {
  engineName: string;              // e.g., 'DeepSeek', 'Mistral', 'Heuristic'
  engineType: 'primary' | 'fallback';
  rules: RuleModel[];
  processingTime?: number;         // milliseconds
  modelVersion?: string;           // e.g., 'v2.1.0'
}

/**
 * Individual rule model
 */
export interface RuleModel {
  id: string;                      // e.g., 'TRC004'
  description: string;             // Human-readable rule description
  engine: string;                  // Which AI engine generated this
  confidence: number;              // 0-100 confidence score
  status: RuleStatus;
  cms_code?: string;               // e.g., 'CMS-1500-02'
  tags?: RuleTag[];                // e.g., ['high-risk', 'manual_stub']
  source_document?: string;        // Source CMS document
  extracted_text?: string;         // Original text from CMS doc
  rule_logic?: string;             // Generated validation logic
  created_at?: Date;
  updated_at?: Date;
  approved_by?: string;            // User who approved
  rejected_by?: string;            // User who rejected
  rejection_reason?: string;       // Why rule was rejected
}

/**
 * Rule status enum
 */
export type RuleStatus = 'pending' | 'approved' | 'rejected' | 'disabled';

/**
 * Predefined rule tags
 */
export type RuleTag = 'high-risk' | 'manual_stub' | 'fallback_used' | 'auto-generated' | 'requires-review';

/**
 * Response from trigger eligibility check
 */
export interface TriggerStatus {
  eligible: boolean;
  reason?: string;                 // If not eligible, why?
  lastRunDate?: Date;
  cmsLastModified?: Date;
  pendingRun?: {
    runId: string;
    status: string;
    startedAt: Date;
  };
}

/**
 * Response from commit operation
 */
export interface CommitResponse {
  success: boolean;
  runId: string;
  committedAt: Date;
  approvedCount: number;
  rejectedCount: number;
  generatedFiles?: {
    cms_rules_yml: string;
    trc_rules_json: string;
    program_rules_json: string;
  };
  message?: string;
}

/**
 * Rule decision for tracking approve/reject actions
 */
export interface RuleDecision {
  ruleId: string;
  status: 'approved' | 'rejected';
  decidedAt: Date;
  decidedBy: string;
  tags?: RuleTag[];
}

/**
 * Progress step for rule run process
 */
export interface ProgressStep {
  step: number;
  name: string;
  status: 'pending' | 'active' | 'complete' | 'failed';
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

/**
 * Rule run progress tracking
 */
export interface RuleRunProgress {
  runId: string;
  planId: string;
  currentStep: number;
  totalSteps: number;
  steps: ProgressStep[];
  estimatedTimeRemaining?: number;  // seconds
}

/**
 * Rule run history
 */
export interface RuleRunHistory {
  runId: string;
  planId: string;
  started: Date;
  completed?: Date;
  status: 'completed' | 'in-progress' | 'failed';
  rulesCount: number;
  approvedCount?: number;
  rejectedCount?: number;
}

/**
 * Error response from API
 */
export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
  timestamp: Date;
  path?: string;
}
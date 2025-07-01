// frontend/src/app/app-routing.module.ts

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: 'admin/rule-landing',
    loadComponent: () => import('./admin/components/rule-landing/rule-landing.component').then(c => c.RuleLandingComponent)
  },
  {
    path: 'admin/rule-review',
    loadComponent: () => import('./admin/components/rule-review/rule-review.component').then(c => c.RuleReviewComponent)
  },
  {
    path: 'admin/rule-commit',
    loadComponent: () => import('./admin/components/rule-commit/rule-commit.component').then(c => c.RuleCommitComponent)
  },
  {
    path: 'admin/rule-past-runs',
    loadComponent: () => import('./admin/components/rule-past-runs/rule-past-runs.component').then(c => c.RulePastRunsComponent)
  },
  {
    path: 'upload',
    loadChildren: () => import('./upload/upload-module').then(m => m.UploadModule)
  },
  {
    path: '',
    redirectTo: '/admin/rule-landing',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/admin/rule-landing'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
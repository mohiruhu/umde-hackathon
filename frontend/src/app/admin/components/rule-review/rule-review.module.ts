import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { RuleReviewComponent } from './rule-review.component';

const routes: Routes = [
  {
    path: '',
    component: RuleReviewComponent
  }
];

@NgModule({
  declarations: [
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    RuleReviewComponent
  ]
})
export class RuleReviewModule {}

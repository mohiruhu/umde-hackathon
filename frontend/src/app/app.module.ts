// Location: frontend/src/app/app.module.ts

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

// Import your existing app component - update path if needed
import { AppComponent } from './app';

// Services
import { RuleRunService } from './admin/services/rule-run.service';

// Interceptor (optional)
import { errorInterceptorProvider } from './core/interceptors/error.interceptor';

// Import your existing routing module
import { AppRoutingModule } from './app-routing.module';

@NgModule({  declarations: [
    AppComponent
  ],  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    CommonModule,
    FormsModule,
    RouterModule,
    AppRoutingModule
  ],
  providers: [
    RuleRunService,
    errorInterceptorProvider // Optional
    // Note: RuleReviewStore is provided at component level, not here
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
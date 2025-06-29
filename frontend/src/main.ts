// Location: frontend/src/main.ts
// Modern Angular 20+ approach with providers

import { bootstrapApplication } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { importProvidersFrom } from '@angular/core';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes'; // You'll need to create this
import { errorInterceptor } from './app/core/interceptors/error.interceptor';
import { RuleRunService } from './app/admin/services/rule-run.service';

bootstrapApplication(AppComponent, {
  providers: [
    // Animations support
    provideAnimations(),
    
    // HTTP client with interceptors
    provideHttpClient(
      withInterceptors([errorInterceptor])
    ),
    
    // Router configuration
    provideRouter(routes),
    
    // Your services (though @Injectable({providedIn: 'root'}) services are auto-provided)
    RuleRunService,
    
    // Legacy module imports if needed
    // importProvidersFrom(SomeModule)
  ]
}).catch(err => console.error(err));
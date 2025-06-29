/**
 * Global HTTP Error Interceptor
 * Location: frontend/src/app/core/interceptors/error.interceptor.ts
 */

import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse,
  HTTP_INTERCEPTORS
} from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { catchError, retry, retryWhen, mergeMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(
    private router: Router
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // List of status codes that should not be retried
    const excludedStatusCodes = [400, 401, 403, 404, 409];
    
    return next.handle(request).pipe(
      // Custom retry logic for newer RxJS
      retryWhen(errors =>
        errors.pipe(
          mergeMap((error, index) => {
            // Don't retry if it's a client error or excluded status code
            if (error instanceof HttpErrorResponse && 
                (excludedStatusCodes.includes(error.status) || 
                 request.method === 'POST' || 
                 request.method === 'PUT' || 
                 request.method === 'DELETE')) {
              return throwError(() => error);
            }
            
            // Retry up to 2 times with 1 second delay
            if (index < 2) {
              return timer(1000);
            }
            
            return throwError(() => error);
          })
        )
      ),
      
      catchError((error: HttpErrorResponse) => {
        let errorMessage = 'An unexpected error occurred';
        
        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMessage = error.error.message;
          console.error('Client Error:', error.error);
        } else {
          // Server-side error
          console.error(`Server Error ${error.status}:`, error.error);
          
          switch (error.status) {
            case 400:
              errorMessage = error.error?.message || 'Invalid request';
              break;
              
            case 401:
              errorMessage = 'Session expired. Please log in again.';
              // Redirect to login
              this.router.navigate(['/login']);
              break;
              
            case 403:
              errorMessage = 'You do not have permission to perform this action';
              break;
              
            case 404:
              errorMessage = 'The requested resource was not found';
              break;
              
            case 409:
              errorMessage = error.error?.message || 'A conflict occurred';
              break;
              
            case 422:
              // Validation errors
              if (error.error?.errors) {
                const errors = Object.values(error.error.errors).flat();
                errorMessage = errors.join(', ');
              } else {
                errorMessage = 'Validation failed';
              }
              break;
              
            case 500:
              errorMessage = 'Server error. Please try again later.';
              break;
              
            case 503:
              errorMessage = 'Service temporarily unavailable';
              break;
              
            default:
              errorMessage = `Error ${error.status}: ${error.statusText}`;
          }
        }

        // Log to console in development
        if (!environment.production) {
          console.error('HTTP Error Details:', {
            url: error.url,
            status: error.status,
            message: errorMessage,
            error: error.error
          });
        }

        // Return user-friendly error
        return throwError(() => ({
          message: errorMessage,
          status: error.status,
          originalError: error
        }));
      })
    );
  }
}

/**
 * Provider configuration for app.module.ts
 */
export const errorInterceptorProvider = {
  provide: HTTP_INTERCEPTORS,
  useClass: ErrorInterceptor,
  multi: true
};
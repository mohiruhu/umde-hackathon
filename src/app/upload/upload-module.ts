import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadRoutingModule } from './upload-routing-module';
import { HttpClientModule } from '@angular/common/http';
import { UploadComponent } from './upload.component'; // ✅

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    UploadRoutingModule,
    UploadComponent // ✅ standalone component goes in `imports`
  ]
})
export class UploadModule {}

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [AppComponent], // ✅ ONLY AppComponent
  imports: [
    BrowserModule,
    RouterModule,
    AppRoutingModule
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}

import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: false, // REMOVE if previously using standalone
  templateUrl: './app.html',
  styleUrls: ['./app.scss'],
})
export class AppComponent {
  constructor() {
    console.log('✅ AppComponent initialized');
  }
}


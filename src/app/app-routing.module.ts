import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: 'upload',
    loadChildren: () =>
      import('./upload/upload-module').then((m) => m.UploadModule)
  },
  {
    path: '',
    redirectTo: 'upload',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}

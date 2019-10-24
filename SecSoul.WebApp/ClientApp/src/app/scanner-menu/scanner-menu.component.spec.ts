import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ScannerMenuComponent } from './scanner-menu.component';

describe('ScannerMenuComponent', () => {
  let component: ScannerMenuComponent;
  let fixture: ComponentFixture<ScannerMenuComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ScannerMenuComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ScannerMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

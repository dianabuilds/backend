/// <reference types="cypress" />

Cypress.on('uncaught:exception', () => {
  // prevent failing tests on unexpected runtime errors surfaced to window
  return false;
});


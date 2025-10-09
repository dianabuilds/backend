export {};

declare global {
  // React testing library toggles this flag to silence act warnings.
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

export default {
  // Application title and navigation
  app_title: 'Nuwa AI Text-to-SQL System',
  
  // Query input component
  query_input_title: 'Natural Language Query',
  query_input_placeholder: 'Enter your query, e.g.: Show all users with their names and emails',
  submit_query: 'Submit Query',
  clear: 'Clear',
  query_input_tip: 'Tip: Use Ctrl+Enter to submit quickly',
  
  // SQL display component
  generated_sql: 'Generated SQL',
  sql_explanation: 'SQL Explanation',
  sql_explanation_example: 'This query selects all user records from the users table that contain the specified keyword',
  copy: 'Copy',
  copied: 'Copied',
  copy_success: 'SQL copied to clipboard',
  copy_failed: 'Copy failed, please copy manually',
  
  // Result table component
  query_results: 'Query Results',
  no_data: 'No data available',
  total_records: 'Total {{count}} records',
  table_pagination: 'Showing {{start}} to {{end}} of {{total}} entries',
  
  // Common fields
  name: 'Name',
  email: 'Email',
  id: 'ID',
  
  // Error messages
  network_error: 'Network error, please check your connection',
  server_error: 'Server error, please try again later',
  invalid_query: 'Invalid query format, please re-enter',
  
  // Loading states
  loading: 'Loading...',
  processing: 'Processing...',
  
  // Button text
  retry: 'Retry',
  cancel: 'Cancel',
  confirm: 'Confirm',
  
  // Operation feedback
  query_success: 'Query successful',
  query_failed: 'Query failed, please try again',
  
  // Language switching
  language_chinese: '中文',
  language_english: 'English',
  
  // API related
  default_explanation: 'This query is used to retrieve data with specified conditions'
};
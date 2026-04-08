// Theme Toggle Functionality
(function() {
  // Get saved theme or default to light
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // Create theme toggle button
  function createThemeToggle() {
    const toggle = document.createElement('button');
    toggle.id = 'themeToggle';
    toggle.className = 'theme-toggle';
    toggle.innerHTML = savedTheme === 'dark' ? '☀️' : '🌙';
    toggle.title = savedTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    toggle.onclick = toggleTheme;
    
    // Add to page
    document.body.appendChild(toggle);
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const toggle = document.getElementById('themeToggle');
    toggle.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
    toggle.title = newTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createThemeToggle);
  } else {
    createThemeToggle();
  }
})();

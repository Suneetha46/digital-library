/**
 * Instant JavaScript Book Search & Dynamic Multi-Filter
 * Searches by Title, Author, Genre, and ISBN in real-time
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('book-live-search');
  const clearBtn = document.getElementById('clear-search-btn');
  const genrePills = document.querySelectorAll('.genre-pill-btn');
  const availabilitySelect = document.getElementById('availability-filter-select');
  const bookCards = document.querySelectorAll('.book-card-item');
  const resultsCounter = document.getElementById('search-results-counter');
  const noResultsBox = document.getElementById('no-results-found');
  const bookCatalogGrid = document.getElementById('book-catalog-grid');

  if (!bookCards.length) return;

  let activeGenre = 'all';
  let activeAvailability = 'all';
  let searchTerm = '';

  // Initialize from URL params if present
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('q')) {
    searchTerm = urlParams.get('q').toLowerCase().trim();
    if (searchInput) searchInput.value = searchTerm;
  }
  if (urlParams.has('genre')) {
    activeGenre = urlParams.get('genre').toLowerCase().trim();
  }
  if (urlParams.has('availability')) {
    activeAvailability = urlParams.get('availability').toLowerCase().trim();
    if (availabilitySelect) availabilitySelect.value = activeAvailability;
  }

  function filterBooks() {
    let visibleCount = 0;
    const term = searchTerm.toLowerCase().trim();

    bookCards.forEach(card => {
      const title = (card.getAttribute('data-title') || '').toLowerCase();
      const author = (card.getAttribute('data-author') || '').toLowerCase();
      const genre = (card.getAttribute('data-genre') || '').toLowerCase();
      const isbn = (card.getAttribute('data-isbn') || '').toLowerCase();
      const availableCopies = parseInt(card.getAttribute('data-copies') || '0', 10);

      // Search term matching
      const matchesSearch = !term ||
        title.includes(term) ||
        author.includes(term) ||
        genre.includes(term) ||
        isbn.includes(term);

      // Genre matching
      const matchesGenre = activeGenre === 'all' || genre === activeGenre.toLowerCase();

      // Availability matching
      let matchesAvailability = true;
      if (activeAvailability === 'available') {
        matchesAvailability = availableCopies > 0;
      } else if (activeAvailability === 'borrowed') {
        matchesAvailability = availableCopies === 0;
      }

      const isVisible = matchesSearch && matchesGenre && matchesAvailability;

      if (isVisible) {
        card.style.display = '';
        card.classList.remove('d-none');
        visibleCount++;
      } else {
        card.style.display = 'none';
        card.classList.add('d-none');
      }
    });

    // Update counter
    if (resultsCounter) {
      resultsCounter.textContent = `Showing ${visibleCount} of ${bookCards.length} titles`;
    }

    // Toggle Empty state
    if (noResultsBox) {
      if (visibleCount === 0) {
        noResultsBox.style.display = 'block';
        if (bookCatalogGrid) bookCatalogGrid.style.display = 'none';
      } else {
        noResultsBox.style.display = 'none';
        if (bookCatalogGrid) bookCatalogGrid.style.display = '';
      }
    }

    // Toggle clear button
    if (clearBtn) {
      clearBtn.style.display = term ? 'inline-flex' : 'none';
    }
  }

  // Event Listeners
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchTerm = e.target.value;
      filterBooks();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        searchTerm = '';
        searchInput.focus();
        filterBooks();
      }
    });
  }

  // Genre pills
  genrePills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      genrePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      activeGenre = pill.getAttribute('data-genre') || 'all';
      filterBooks();
    });
  });

  // Availability dropdown
  if (availabilitySelect) {
    availabilitySelect.addEventListener('change', (e) => {
      activeAvailability = e.target.value;
      filterBooks();
    });
  }

  // Initial execution
  filterBooks();
});

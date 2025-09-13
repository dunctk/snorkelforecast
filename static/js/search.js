document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById('autoComplete');
  const searchLoading = document.getElementById('search-loading');
  const searchButton = document.getElementById('search-button');

  // Show loading state
  function showLoading() {
    searchLoading.classList.remove('hidden');
  }

  // Hide loading state
  function hideLoading() {
    searchLoading.classList.add('hidden');
  }

  const autoCompleteJS = new autoComplete({
    selector: "#autoComplete",
    placeHolder: "Search for a location...",
    data: {
      src: async (query) => {
        try {
          showLoading();
          const source = await fetch(`/api/search-locations/?q=${query}`);
          const data = await source.json(); // This is the dictionary grouped by country

          // Flatten the data and add a 'group' key for country
          const flattenedData = [];
          for (const countryName in data) {
            if (data.hasOwnProperty(countryName)) {
              data[countryName].forEach(location => {
                flattenedData.push({
                  ...location,
                  group: countryName // Add a group key for later use
                });
              });
            }
          }
          return flattenedData; // Return the flattened array
        } catch (error) {
          console.error('Search error:', error);
          return [];
        } finally {
          hideLoading();
        }
      },
      keys: ["city"],
      cache: false,
    },
    resultsList: {
      element: (list, data) => {
        // Add custom styling to the results list
        list.classList.add('bg-white', 'ui-night:bg-gray-800', 'border', 'border-gray-200', 'ui-night:border-gray-700', 'rounded-lg', 'shadow-xl', 'mt-2', 'max-h-80', 'overflow-y-auto');

        const info = document.createElement("p");
        info.classList.add('px-4', 'py-2', 'text-sm', 'text-gray-600', 'ui-night:text-gray-400', 'border-b', 'border-gray-200', 'ui-night:border-gray-700', 'bg-gray-50', 'ui-night:bg-gray-900');
        if (data.results.length > 0) {
          info.innerHTML = `Displaying <strong>${data.results.length}</strong> out of <strong>${data.matches.length}</strong> results`;
        } else {
          info.innerHTML = `Found <strong>${data.matches.length}</strong> matching results for <strong>"${data.query}"</strong>`;
        }
        list.prepend(info);
      },
      noResults: (list, query) => {
        const message = document.createElement("div");
        message.classList.add('px-4', 'py-8', 'text-center', 'text-gray-500', 'ui-night:text-gray-400');
        message.innerHTML = `
          <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.5 9.5l4 4"></path>
          </svg>
          <p class="text-sm">No locations found for "<strong>${query}</strong>"</p>
          <p class="text-xs mt-1">Try searching for a different location or browse by country below.</p>
        `;
        list.appendChild(message);
      },
      maxResults: 15,
      tabSelect: true,
      groupBy: "group", // Group results by the 'group' key (country name)
    },
    resultItem: {
      element: (item, data) => {
        // Modify the item's HTML to display city and country with better styling
        item.classList.add('px-4', 'py-3', 'hover:bg-gray-50', 'ui-night:hover:bg-gray-700', 'cursor-pointer', 'border-b', 'border-gray-100', 'ui-night:border-gray-700', 'last:border-b-0');
        item.innerHTML = `
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <span class="font-semibold text-gray-900 ui-night:text-white">${data.value.city}</span>
              <span class="text-sm text-gray-500 ui-night:text-gray-400 ml-2">${data.value.group}</span>
            </div>
            <svg class="h-4 w-4 text-gray-400 ui-night:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </div>
        `;
      },
      highlight: {
        render: true
      },
    },
    events: {
      input: {
        focus: () => {
          if (autoCompleteJS.input.value.length) autoCompleteJS.start();
        },
      },
    },
    onSelection: (feedback) => {
      const selection = feedback.selection.value;
      window.location.href = `/${selection.country_slug}/${selection.slug}/`;
    },
  });

  // Handle search button click
  if (searchButton) {
    searchButton.addEventListener('click', () => {
      const query = searchInput.value.trim();
      if (query) {
        // Trigger search if there's a query
        showLoading();
        autoCompleteJS.start();
        setTimeout(hideLoading, 1000); // Fallback hide loading
      } else {
        // Focus the input if empty
        searchInput.focus();
      }
    });
  }

  // Handle Enter key in search input
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const query = searchInput.value.trim();
      if (query) {
        // If there are results, select the first one
        const results = autoCompleteJS.results;
        if (results && results.length > 0) {
          autoCompleteJS.select(0);
        } else {
          // Show feedback if no results
          showSearchFeedback('No results found. Try a different search term.');
        }
      }
    }
  });

  // Add search feedback function
  function showSearchFeedback(message) {
    // Remove existing feedback
    const existingFeedback = document.getElementById('search-feedback');
    if (existingFeedback) {
      existingFeedback.remove();
    }

    // Create feedback element
    const feedback = document.createElement('div');
    feedback.id = 'search-feedback';
    feedback.className = 'mt-2 px-4 py-2 bg-blue-50 ui-night:bg-blue-900/20 border border-blue-200 ui-night:border-blue-800 rounded-lg text-sm text-blue-700 ui-night:text-blue-300';
    feedback.innerHTML = `
      <div class="flex items-center gap-2">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        ${message}
      </div>
    `;

    // Insert after search container
    const searchContainer = document.querySelector('.search-container') || searchInput.parentElement.parentElement;
    searchContainer.appendChild(feedback);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (feedback.parentElement) {
        feedback.remove();
      }
    }, 3000);
  }

  // Clear feedback when user starts typing
  searchInput.addEventListener('input', () => {
    const feedback = document.getElementById('search-feedback');
    if (feedback) {
      feedback.remove();
    }
  });
});

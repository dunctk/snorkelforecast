document.addEventListener("DOMContentLoaded", function () {
  const autoCompleteJS = new autoComplete({
    selector: "#autoComplete",
    placeHolder: "Search for a location...",
    data: {
      src: async (query) => {
        try {
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
          return error;
        }
      },
      keys: ["city"],
      cache: false,
    },
    resultsList: {
      element: (list, data) => {
        const info = document.createElement("p");
        if (data.results.length > 0) {
          info.innerHTML = `Displaying <strong>${data.results.length}</strong> out of <strong>${data.matches.length}</strong> results`;
        } else {
          info.innerHTML = `Found <strong>${data.matches.length}</strong> matching results for <strong>\"${data.query}\"</strong>`;
        }
        list.prepend(info);
      },
      noResults: true,
      maxResults: 15,
      tabSelect: true,
      groupBy: "group", // Group results by the 'group' key (country name)
    },
    resultItem: {
      element: (item, data) => {
        // Modify the item's HTML to display city and country
        item.innerHTML = `
          <span class="font-semibold">${data.value.city}</span>
          <span class="text-sm text-gray-500">${data.value.group}</span>
        `;
      },
      highlight: true,
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
});

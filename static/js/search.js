document.addEventListener("DOMContentLoaded", function () {
  const autoCompleteJS = new autoComplete({
    selector: "#autoComplete",
    placeHolder: "Search for a location...",
    data: {
      src: async (query) => {
        try {
          const source = await fetch(`/api/search-locations/?q=${query}`);
          const data = await source.json();
          return data;
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
    },
    resultItem: {
      element: (item, data) => {
        item.style = "display: flex; justify-content: space-between;";
        item.innerHTML = `
        <span style=\"text-overflow: ellipsis; white-space: nowrap; overflow: hidden;\">
          ${data.match}
        </span>
        <span style=\"display: flex; align-items: center; font-size: 13px; font-weight: 100; text-transform: uppercase; color: rgba(0,0,0,.5);\">
          ${data.key}
        </span>`;
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

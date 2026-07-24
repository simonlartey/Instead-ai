const SELECTORS = {
  conversation: "#dashboard-conversation",
  profileMenu: "[data-profile-menu]",
  profileMenuTrigger:
    "[data-profile-menu-trigger]",
  profileMenuPopover:
    "[data-profile-menu-popover]",
  locationLabel: "[data-current-location-label]",
  locationSelector: "[data-location-selector]",
  locationPanel: "[data-location-panel]",
  currentLocationButton:
    "[data-current-location-button]",
  locationAutocomplete:
    "[data-location-autocomplete]",
  locationStatus: "[data-location-status]",
  filterChip: "[data-filter]",
  recommendationCard: "[data-recommendation-card]",
  recommendationList: ".recommendation-list",
  mapContainer: "[data-map-container]",
  mapState: "[data-map-state]",
  placeSaveButton: "[data-place-save-button]",
  sidebarShell: "#dashboard-shell",
  dashboardSidebar: "#dashboard-sidebar",
  dashboardInspector: "#dashboard-inspector",
  sidebarToggle: "[data-sidebar-toggle]",
  sidebarToggleIcon: "[data-sidebar-toggle-icon]",
  mobileSidebarToggle: "[data-mobile-sidebar-toggle]",
  sidebarBackdrop: "[data-sidebar-backdrop]",
  inspectorTab: "[data-inspector-tab]",
  inspectorPanel: "[data-inspector-panel]",
  placeResult: "[data-place-result]",
  inspectorResultsList: ".inspector-results-list",
  mobileInspectorToggle: "[data-mobile-inspector-toggle]",
  mobileInspectorClose: "[data-mobile-inspector-close]",
  inspectorBackdrop: "[data-inspector-backdrop]",
  searchForm: "#dashboard-search-form",
  searchInput: "#dashboard-query",
  searchSubmit: "#dashboard-search-submit",
  newChatButton: "[data-new-chat-button]",
  searchStatus: "#dashboard-search-status",
  searchProgress: ".search-progress",
  searchProgressTitle: "#search-progress-title",
  searchProgressStatus: ".search-progress-status",
  searchProgressItems: ".search-progress-list li",
  resultsState: "#dashboard-results-state",
  resultsStateTitle: "[data-results-state-title]",
  resultsStateMessage: "[data-results-state-message]",
  placeHero: "[data-place-hero]",
  placeGallery: "[data-place-gallery]",
  placePhotoAttribution:
    "[data-place-photo-attribution]",
  placeDirectionsAction:
    "[data-place-directions-action]",
  placeCallAction:
    "[data-place-call-action]",
  placeWebsiteAction:
    "[data-place-website-action]",
  dashboardView: "[data-dashboard-view]",
  dashboardNavigation:
    "[data-dashboard-navigation]",
  savedPlacesList:
    "[data-saved-places-list]",
  savedPlacesEmpty:
    "[data-saved-places-empty]",
  savedPlacesExplore:
    "[data-saved-places-explore]",
  discoveryLocation:
    "[data-discovery-location]",
  discoveryMoodGrid:
    "[data-discovery-mood-grid]",
  discoveryCollections:
    "[data-discovery-collections]",
  discoveryQuery:
    "[data-discovery-query]",
  discoveryStatus:
    "[data-discovery-status]",
  discoveryStatusTitle:
    "[data-discovery-status-title]",
  discoveryStatusMessage:
    "[data-discovery-status-message]",
};

const DEFAULT_LOCATION = Object.freeze({
  label: "Portland, ME",
  latitude: 43.6591,
  longitude: -70.2568,
});

const LOCATION_STORAGE_KEY =
  "cityguide:selected-location";

const SAVED_PLACES_STORAGE_KEY =
  "cityguide:saved-place-ids";

const SAVED_PLACE_RECORDS_STORAGE_KEY =
  "cityguide:saved-places";

const SEARCH_TIMEOUT_MILLISECONDS = 30000;

const DISCOVERY_MOODS = Object.freeze([
  {
    id: "eat",
    title: "Eat",
    description: "Find something worth craving.",
    icon: "utensils",
    query:
      "Help me find somewhere great to eat nearby",
    tone: "food",
  },
  {
    id: "relax",
    title: "Relax",
    description: "Slow down somewhere comfortable.",
    icon: "coffee",
    query:
      "Find relaxing cafés, parks, or peaceful places nearby",
    tone: "relax",
  },
  {
    id: "explore",
    title: "Explore",
    description: "See something new today.",
    icon: "compass",
    query:
      "Show me interesting places and experiences to explore nearby",
    tone: "explore",
  },
  {
    id: "shop",
    title: "Shop",
    description: "Discover useful and unique local stores.",
    icon: "shopping-bag",
    query:
      "Find interesting local shops and useful stores nearby",
    tone: "shop",
  },
]);

const isValidStoredLocation = (location) =>
  typeof location?.label === "string" &&
  location.label.trim().length > 0 &&
  Number.isFinite(location.latitude) &&
  Number.isFinite(location.longitude) &&
  location.latitude >= -90 &&
  location.latitude <= 90 &&
  location.longitude >= -180 &&
  location.longitude <= 180;

const loadStoredLocation = () => {
  try {
    const storedValue = window.localStorage.getItem(
      LOCATION_STORAGE_KEY
    );

    if (!storedValue) {
      return null;
    }

    const parsedLocation = JSON.parse(storedValue);

    if (!isValidStoredLocation(parsedLocation)) {
      window.localStorage.removeItem(
        LOCATION_STORAGE_KEY
      );

      return null;
    }

    return {
      label: parsedLocation.label.trim(),
      latitude: parsedLocation.latitude,
      longitude: parsedLocation.longitude,
    };
  } catch (error) {
    console.warn(
      "CityGuide could not restore the saved location:",
      error
    );

    return null;
  }
};

const saveSelectedLocation = (location) => {
  try {
    window.localStorage.setItem(
      LOCATION_STORAGE_KEY,
      JSON.stringify(location)
    );
  } catch (error) {
    console.warn(
      "CityGuide could not save the selected location:",
      error
    );
  }
};

const loadSavedPlaceIds = () => {
  try {
    const storedValue = window.localStorage.getItem(
      SAVED_PLACES_STORAGE_KEY
    );

    if (!storedValue) {
      return new Set();
    }

    const parsedValue = JSON.parse(storedValue);

    if (!Array.isArray(parsedValue)) {
      window.localStorage.removeItem(
        SAVED_PLACES_STORAGE_KEY
      );

      return new Set();
    }

    return new Set(
      parsedValue.filter(
        (placeId) =>
          typeof placeId === "string" &&
          placeId.trim().length > 0
      )
    );
  } catch (error) {
    console.warn(
      "CityGuide could not restore saved places:",
      error
    );

    return new Set();
  }
};

const persistSavedPlaceIds = (savedPlaceIds) => {
  try {
    window.localStorage.setItem(
      SAVED_PLACES_STORAGE_KEY,
      JSON.stringify(Array.from(savedPlaceIds))
    );
  } catch (error) {
    console.warn(
      "CityGuide could not save places:",
      error
    );
  }
};

const loadSavedPlaceRecords = () => {
  try {
    const storedValue = window.localStorage.getItem(
      SAVED_PLACE_RECORDS_STORAGE_KEY
    );

    if (!storedValue) {
      return {};
    }

    const parsedValue = JSON.parse(storedValue);

    if (
      !parsedValue ||
      typeof parsedValue !== "object" ||
      Array.isArray(parsedValue)
    ) {
      window.localStorage.removeItem(
        SAVED_PLACE_RECORDS_STORAGE_KEY
      );

      return {};
    }

    return parsedValue;
  } catch (error) {
    console.warn(
      "CityGuide could not restore saved place details:",
      error
    );

    return {};
  }
};

const persistSavedPlaceRecords = (records) => {
  try {
    window.localStorage.setItem(
      SAVED_PLACE_RECORDS_STORAGE_KEY,
      JSON.stringify(records)
    );
  } catch (error) {
    console.warn(
      "CityGuide could not save place details:",
      error
    );
  }
};

const createSavedPlaceRecord = (place) => ({
  id: place.id,
  name: place.name,
  description: place.description,
  category: place.category,
  tags: Array.isArray(place.tags)
    ? place.tags
    : [],
  rating: place.rating,
  review_count: place.review_count,
  distance_miles: place.distance_miles,
  price_level: place.price_level,
  open_now: place.open_now,
  address: place.address,
  phone: place.phone,
  website: place.website,
  hours_text: place.hours_text,
  photos: Array.isArray(place.photos)
    ? place.photos
    : [],
  match_reasons: Array.isArray(place.match_reasons)
    ? place.match_reasons
    : [],
  latitude: place.latitude,
  longitude: place.longitude,
});

const persistSavedPlaceRecord = (place) => {
  if (!place?.id) {
    return;
  }

  const records = loadSavedPlaceRecords();

  records[place.id] =
    createSavedPlaceRecord(place);

  persistSavedPlaceRecords(records);
};

const removeSavedPlaceRecord = (placeId) => {
  const records = loadSavedPlaceRecords();

  if (!(placeId in records)) {
    return;
  }

  delete records[placeId];

  persistSavedPlaceRecords(records);
};

const isPlaceSaved = (placeId) =>
  loadSavedPlaceIds().has(placeId);

const updateSavedPlaceButtons = (placeId) => {
  if (!placeId) {
    return;
  }

  const place = PLACES[placeId];
  const saved = isPlaceSaved(placeId);
  const placeName = place?.name || "place";

  document
    .querySelectorAll(SELECTORS.placeSaveButton)
    .forEach((button) => {
      if (button.dataset.placeId !== placeId) {
        return;
      }

      button.classList.toggle(
        "place-save-control--saved",
        saved
      );

      button.setAttribute(
        "aria-pressed",
        String(saved)
      );

      button.setAttribute(
        "aria-label",
        saved
          ? `Remove ${placeName} from saved places`
          : `Save ${placeName}`
      );

      const label = button.querySelector(
        "[data-place-save-label]"
      );

      if (label) {
        label.textContent = saved ? "Saved" : "Save";
      }
    });
};

const toggleSavedPlace = (placeId) => {
  if (!placeId) {
    return false;
  }

  const savedPlaceIds = loadSavedPlaceIds();
  let saved;

  if (savedPlaceIds.has(placeId)) {
    savedPlaceIds.delete(placeId);
    removeSavedPlaceRecord(placeId);
    saved = false;
  } else {
    const place = PLACES[placeId];

    if (!place) {
      return false;
    }

    savedPlaceIds.add(placeId);
    persistSavedPlaceRecord(place);
    saved = true;
  }

  persistSavedPlaceIds(savedPlaceIds);
  updateSavedPlaceButtons(placeId);

  if (activeDashboardView === "saved") {
    renderSavedPlacesView();
  }

  return saved;
};

const initializeSavedPlaces = () => {
  document.addEventListener("click", (event) => {
    const button = event.target.closest(
      SELECTORS.placeSaveButton
    );

    if (!button || button.disabled) {
      return;
    }

    const placeId = button.dataset.placeId;

    if (!placeId) {
      return;
    }

    toggleSavedPlace(placeId);
  });
};

let selectedLocation =
  loadStoredLocation() || {
    ...DEFAULT_LOCATION,
  };

let PLACES = {};
let activeDashboardView = "explore";
let discoveryCacheKey = null;
let discoveryMoodPreviews = new Map();
let discoverySections = [];
let discoveryRequestId = 0;
let latestSearchRequestId = 0;
let activeSearchSessionId = null;
let dashboardMap = null;
let mapsLibraryPromise = null;
let placeMapMarkers = new Map();
let selectedMapPlaceId = null;
let latestHeroPhotoRequestId = 0;

const updateLocationLabels = () => {
  document
    .querySelectorAll(SELECTORS.locationLabel)
    .forEach((element) => {
      element.textContent = selectedLocation.label;
    });
};

const resetSearchComposer = () => {
  const input = document.querySelector(
    SELECTORS.searchInput
  );

  const submitButton = document.querySelector(
    SELECTORS.searchSubmit
  );

  if (input) {
    input.disabled = false;
    input.value = "";
  }

  if (submitButton) {
    submitButton.disabled = true;
  }
};

const setSelectedLocation = ({
  label,
  latitude,
  longitude,
}) => {
  if (
    typeof label !== "string" ||
    !label.trim() ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    throw new TypeError(
      "A valid location label and coordinates are required."
    );
  }

  activeSearchSessionId = null;
  latestSearchRequestId += 1;
  resetSearchComposer();

  selectedLocation = {
    label: label.trim(),
    latitude,
    longitude,
  };

  saveSelectedLocation(selectedLocation);
  updateLocationLabels();
  updateDiscoveryLocation();

  discoveryCacheKey = null;
  discoveryMoodPreviews = new Map();
  discoverySections = [];
  discoveryRequestId += 1;

  if (activeDashboardView === "categories") {
    void renderDiscoveryHub({
      force: true,
    });
  }

  if (dashboardMap) {
    dashboardMap.setCenter({
      lat: latitude,
      lng: longitude,
    });

    dashboardMap.setZoom(13);
  }
};

const getAddressComponent = (
  addressComponents,
  type,
  nameField = "long_name"
) => {
  if (!Array.isArray(addressComponents)) {
    return null;
  }

  const component = addressComponents.find(
    (item) =>
      Array.isArray(item?.types) &&
      item.types.includes(type)
  );

  const value = component?.[nameField];

  if (
    typeof value !== "string" ||
    !value.trim()
  ) {
    return null;
  }

  return value.trim();
};

const getLocationLabel = async ({
  latitude,
  longitude,
}) => {
  const { Geocoder } =
    await window.google.maps.importLibrary(
      "geocoding"
    );

  const geocoder = new Geocoder();

  const { results } = await geocoder.geocode({
    location: {
      lat: latitude,
      lng: longitude,
    },
  });

  const result = results?.[0];
  const addressComponents =
    result?.address_components;

  const city =
    getAddressComponent(
      addressComponents,
      "locality"
    ) ||
    getAddressComponent(
      addressComponents,
      "postal_town"
    ) ||
    getAddressComponent(
      addressComponents,
      "administrative_area_level_2"
    );

  const state =
    getAddressComponent(
      addressComponents,
      "administrative_area_level_1",
      "short_name"
    ) ||
    getAddressComponent(
      addressComponents,
      "administrative_area_level_1"
    );

  if (city && state) {
    return `${city}, ${state}`;
  }

  if (city) {
    return city;
  }

  if (state) {
    return state;
  }

  if (
    typeof result?.formatted_address === "string" &&
    result.formatted_address.trim()
  ) {
    return result.formatted_address.trim();
  }

  return `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
};

const getGeolocationErrorMessage = (error) => {
  if (error?.code === 1) {
    return (
      "Location permission was denied. " +
      "Choose a location manually instead."
    );
  }

  if (error?.code === 2) {
    return (
      "Your current location could not be determined. " +
      "Choose a location manually instead."
    );
  }

  if (error?.code === 3) {
    return (
      "Finding your current location took too long. " +
      "Please try again."
    );
  }

  return "CityGuide could not access your current location.";
};

const hydrateDashboardIcons = () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
};

const loadGoogleMapsLibrary = () => {
  if (mapsLibraryPromise) {
    return mapsLibraryPromise;
  }

  const container = document.querySelector(
    SELECTORS.mapContainer
  );

  const apiKey =
    container?.dataset.mapsApiKey?.trim();

  if (!container || !apiKey) {
    return Promise.reject(
      new Error("Google Maps is not configured.")
    );
  }

  if (window.google?.maps?.importLibrary) {
    mapsLibraryPromise = Promise.resolve(
      window.google.maps
    );

    return mapsLibraryPromise;
  }

  mapsLibraryPromise = new Promise(
    (resolve, reject) => {
      const callbackName =
        "__cityGuideGoogleMapsLoaded";

      const script = document.createElement("script");

      const params = new URLSearchParams({
        key: apiKey,
        callback: callbackName,
        loading: "async",
        v: "weekly",
      });

      window[callbackName] = () => {
        delete window[callbackName];

        if (!window.google?.maps?.importLibrary) {
          mapsLibraryPromise = null;

          reject(
            new Error(
              "Google Maps loaded without the expected API."
            )
          );

          return;
        }

        resolve(window.google.maps);
      };

      script.src =
        "https://maps.googleapis.com/maps/api/js?" +
        params.toString();

      script.async = true;
      script.defer = true;

      script.addEventListener("error", () => {
        delete window[callbackName];
        mapsLibraryPromise = null;
        script.remove();

        reject(
          new Error("Google Maps could not load.")
        );
      });

      document.head.append(script);
    }
  );

  return mapsLibraryPromise;
};

const initializeInteractiveMap = async () => {
  const container = document.querySelector(
    SELECTORS.mapContainer
  );

  const state = document.querySelector(
    SELECTORS.mapState
  );

  if (!container) {
    return null;
  }

  if (dashboardMap) {
    return dashboardMap;
  }

  if (state) {
    state.textContent =
      "Loading interactive map...";
    state.classList.remove(
      "map-loading-state--error"
    );
  }

  try {
    await loadGoogleMapsLibrary();

    const { Map } =
      await window.google.maps.importLibrary(
        "maps"
      );

    const { ColorScheme } =
      await window.google.maps.importLibrary(
        "core"
      );

    const mapOptions = {
      center: {
        lat: selectedLocation.latitude,
        lng: selectedLocation.longitude,
      },
      zoom: 13,
      colorScheme: ColorScheme.DARK,
      disableDefaultUI: true,
      zoomControl: true,
      clickableIcons: false,
    };

    const mapId =
      container.dataset.mapId?.trim();

    if (mapId) {
      mapOptions.mapId = mapId;
    }

    dashboardMap = new Map(
      container,
      mapOptions
    );

    state?.remove();

    return dashboardMap;
  } catch (error) {
    mapsLibraryPromise = null;

    if (state) {
      state.textContent =
        "The interactive map is temporarily unavailable.";

      state.classList.add(
        "map-loading-state--error"
      );
    }

    console.error(
      "CityGuide map failed to load:",
      error
    );

    return null;
  }
};

const getPlaceCoordinates = (place) => {
  const latitude = Number(place?.latitude);
  const longitude = Number(place?.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return {
    lat: latitude,
    lng: longitude,
  };
};

const clearMapMarkers = () => {
  placeMapMarkers.forEach(({ marker }) => {
    marker.map = null;
  });

  placeMapMarkers.clear();
  selectedMapPlaceId = null;
};

const updateSelectedMapMarker = (placeId) => {
  selectedMapPlaceId = placeId;

  placeMapMarkers.forEach(
    ({ marker, pin }, markerPlaceId) => {
      const isSelected =
        markerPlaceId === placeId;

      pin.background = isSelected
        ? "#d88a22"
        : "#16252d";

      pin.borderColor = isSelected
        ? "#f7b84b"
        : "#d88a22";

      pin.glyphColor = "#ffffff";

      marker.zIndex = isSelected ? 1000 : 1;
    }
  );
};

const formatMessageTime = (date = new Date()) =>
  new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);

const createMessageAvatar = (role) => {
  const avatar = document.createElement("div");

  avatar.className =
    `message-avatar message-avatar--${role}`;

  if (role === "user") {
    avatar.textContent = "SL";
    avatar.setAttribute(
      "aria-label",
      "Simon Lartey"
    );

    return avatar;
  }

  const logo = document.createElement("img");

  logo.className = "message-avatar-logo";
  logo.src =
    "/static/images/instead-logo.svg";
  logo.alt = "";
  logo.setAttribute("aria-hidden", "true");

  avatar.append(logo);
  avatar.setAttribute("aria-hidden", "true");

  return avatar;
};

const createConversationMessage = ({
  role,
  text,
  pending = false,
}) => {
  const row = document.createElement("div");

  row.className =
    `message-row message-row--${role}`;

  const bubble = document.createElement("article");

  bubble.className =
    `message-bubble message-bubble--${role}`;

  const message = document.createElement("p");
  message.textContent = text;

  // Add a visually hidden sender label for screen readers
  const sender = document.createElement("span");
  sender.className = "sr-only";
  sender.textContent = role === "user" ? "You:" : "Instead:";

  const time = document.createElement("time");
  const now = new Date();

  time.dateTime = now.toISOString();
  time.textContent = formatMessageTime(now);

  bubble.append(sender, message, time);

  if (pending) {
    bubble.dataset.pendingMessage = "";
    bubble.setAttribute("aria-busy", "true");
  }

  const avatar = createMessageAvatar(role);

  if (role === "user") {
    row.append(bubble, avatar);
  } else {
    row.append(avatar, bubble);
  }

  return {
    row,
    bubble,
    message,
  };
};

const scrollConversationToLatest = () => {
  const conversation = document.querySelector(
    SELECTORS.conversation
  );

  if (!conversation) {
    return;
  }

  conversation.lastElementChild?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
};

const appendConversationMessage = ({
  role,
  text,
  pending = false,
}) => {
  const conversation = document.querySelector(
    SELECTORS.conversation
  );

  if (!conversation) {
    return null;
  }

  const renderedMessage = createConversationMessage({
    role,
    text,
    pending,
  });

  conversation.append(renderedMessage.row);
  scrollConversationToLatest();

  return renderedMessage;
};

const updateConversationMessage = (
  renderedMessage,
  text
) => {
  if (!renderedMessage) {
    return;
  }

  renderedMessage.message.textContent = text;
  renderedMessage.bubble.removeAttribute(
    "data-pending-message"
  );
  renderedMessage.bubble.setAttribute(
    "aria-busy",
    "false"
  );

  scrollConversationToLatest();
};

const buildSearchResultMessage = (
  query,
  resultCount
) => {
  const resultLabel =
    resultCount === 1 ? "place" : "places";

  return (
    `I found ${resultCount} ${resultLabel} matching ` +
    `“${query}” near ${selectedLocation.label}. ` +
    "Here are the local options I found."
  );
};

const formatPriceLevel = (priceLevel) => {
  if (!Number.isInteger(priceLevel) || priceLevel < 1) {
    return "";
  }

  return "$".repeat(priceLevel);
};

const formatRating = (rating) => {
  if (typeof rating !== "number") {
    return "Not rated";
  }

  return String(rating);
};

const formatDistance = (distanceMiles) => {
  if (typeof distanceMiles !== "number") {
    return "Distance unavailable";
  }

  return `${distanceMiles} mi`;
};

const formatOpenStatus = (openNow) => {
  if (openNow === true) {
    return "Open now";
  }

  if (openNow === false) {
    return "Closed";
  }

  return "Hours unavailable";
};

const buildDirectionsUrl = (place) => {
  if (
    typeof place.maps_url === "string" &&
    place.maps_url.trim()
  ) {
    return place.maps_url;
  }

  if (
    typeof place.latitude === "number" &&
    typeof place.longitude === "number"
  ) {
    const destination =
      `${place.latitude},${place.longitude}`;

    return (
      "https://www.google.com/maps/dir/?" +
      new URLSearchParams({
        api: "1",
        destination,
      }).toString()
    );
  }

  return null;
};

const buildPhoneUrl = (phone) => {
  if (typeof phone !== "string" || !phone.trim()) {
    return null;
  }

  const normalizedPhone = phone.replace(
    /[^\d+]/g,
    ""
  );

  return normalizedPhone
    ? `tel:${normalizedPhone}`
    : null;
};

const buildWebsiteUrl = (website) => {
  if (typeof website !== "string" || !website.trim()) {
    return null;
  }

  try {
    const url = new URL(website);

    return ["http:", "https:"].includes(url.protocol)
      ? url.toString()
      : null;
  } catch {
    return null;
  }
};

const createPlaceAction = ({
  iconName,
  label,
  ariaLabel = label,
  url,
}) => {
  if (!url) {
    const button = document.createElement("button");

    button.type = "button";
    button.disabled = true;
    button.setAttribute(
      "aria-label",
      `${ariaLabel} unavailable`
    );

    const icon = document.createElement("span");
    icon.setAttribute("aria-hidden", "true");
    icon.setAttribute("data-lucide", iconName);

    button.append(
      icon,
      document.createTextNode(label)
    );

    return button;
  }

  const link = document.createElement("a");

  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.setAttribute(
    "aria-label",
    ariaLabel
  );

  if (url.startsWith("tel:")) {
    link.removeAttribute("target");
    link.removeAttribute("rel");
  }

  const icon = document.createElement("span");
  icon.setAttribute("aria-hidden", "true");
  icon.setAttribute("data-lucide", iconName);

  link.append(
    icon,
    document.createTextNode(label)
  );

  return link;
};

const updatePlaceAction = (
  element,
  {
    url,
    label,
    openInNewTab = true,
  }
) => {
  if (!element) {
    return;
  }

  element.setAttribute("aria-label", label);

  if (!url) {
    element.removeAttribute("href");
    element.removeAttribute("target");
    element.removeAttribute("rel");
    element.setAttribute("aria-disabled", "true");
    element.tabIndex = -1;
    return;
  }

  element.href = url;
  element.removeAttribute("aria-disabled");
  element.tabIndex = 0;

  if (openInNewTab) {
    element.target = "_blank";
    element.rel = "noopener noreferrer";
  } else {
    element.removeAttribute("target");
    element.removeAttribute("rel");
  }
};

const buildPlacePhotoUrl = (
  photo,
  width = 800
) => {
  const photoName = photo?.name;

  if (
    typeof photoName !== "string" ||
    photoName.trim().length === 0
  ) {
    return null;
  }

  const params = new URLSearchParams({
    name: photoName,
    width: String(width),
  });

  return `/api/v1/place-photo?${params.toString()}`;
};

const getPhotoAttributionNames = (photo) => {
  const attributions = photo?.author_attributions;

  if (!Array.isArray(attributions)) {
    return [];
  }

  return attributions
    .map((attribution) => attribution?.displayName)
    .filter(
      (name) =>
        typeof name === "string" &&
        name.trim().length > 0
    );
};

const getRecommendationImageClass = (index) => {
  const imageClasses = [
    "recommendation-image--one",
    "recommendation-image--two",
    "recommendation-image--three",
  ];

  return imageClasses[index % imageClasses.length];
};

const normalizePlaceForDashboard = (place, index) => ({
  ...place,
  rating: place.rating,
  ratingLabel: formatRating(place.rating),
  distance: formatDistance(place.distance_miles),
  price:
    formatPriceLevel(place.price_level) ||
    "Price unavailable",
  status: formatOpenStatus(place.open_now),
  hours: place.hours_text || "Hours unavailable",
  primaryPhoto:
    Array.isArray(place.photos) &&
    place.photos.length > 0
      ? place.photos[0]
      : null,
  photos: Array.isArray(place.photos) ? place.photos : [],
  heroClass: getRecommendationImageClass(index).replace(
    "recommendation-image",
    "place-hero"
  ),
  reasons: Array.isArray(place.match_reasons)
    ? place.match_reasons
    : [],
});

const updateCurrentPlaces = (places) => {
  const normalizedPlaces = places.map(
    normalizePlaceForDashboard
  );

  PLACES = Object.fromEntries(
    normalizedPlaces.map((place) => [
      place.id,
      place,
    ])
  );

  const savedPlaceIds = loadSavedPlaceIds();

  normalizedPlaces.forEach((place) => {
    if (savedPlaceIds.has(place.id)) {
      persistSavedPlaceRecord(place);
    }
  });

  return normalizedPlaces;
};

const createRecommendationCard = (place, index) => {
  const card = document.createElement("article");

  card.className = "recommendation-card";
  card.dataset.recommendationCard = "";
  card.dataset.placeId = place.id;
  card.tabIndex = 0;

  if (index === 0) {
    card.classList.add("recommendation-card--selected");
  }

  const image = document.createElement("div");
  image.className =
    `recommendation-image ${getRecommendationImageClass(index)}`;

  const photoUrl = buildPlacePhotoUrl(
    place.primaryPhoto,
    800
  );

  if (photoUrl) {
    const photo = document.createElement("img");
    const authorAttributions =
      place.primaryPhoto?.author_attributions;

    photo.className = "recommendation-photo";
    photo.src = photoUrl;
    photo.alt = `${place.name} location`;
    photo.loading = "lazy";
    photo.decoding = "async";

    if (
      Array.isArray(authorAttributions) &&
      authorAttributions.length > 0
    ) {
      const names = authorAttributions
        .map((attribution) => attribution?.displayName)
        .filter(Boolean);

      if (names.length > 0) {
        photo.dataset.photoAttribution =
          names.join(", ");
      }
    }

    photo.addEventListener("error", () => {
      photo.remove();

      image.classList.remove(
        "recommendation-image--has-photo"
      );
    });

    image.classList.add(
      "recommendation-image--has-photo"
    );
    image.append(photo);
  }

  const rank = document.createElement("span");
  rank.className = "recommendation-rank";
  rank.textContent = String(index + 1);

  const imageLabel = document.createElement("span");
  imageLabel.className = "recommendation-image-label";
  imageLabel.setAttribute("aria-hidden", "true");
  imageLabel.textContent = `${place.name} preview`;

  image.append(rank, imageLabel);

  const copy = document.createElement("div");
  copy.className = "recommendation-copy";

  const heading = document.createElement("div");
  heading.className = "recommendation-heading";

  const headingCopy = document.createElement("div");

  const name = document.createElement("h2");
  name.textContent = place.name;

  const meta = document.createElement("div");
  meta.className = "recommendation-meta";

  const rating = document.createElement("span");
  rating.className = "rating";
  if (typeof place.rating === "number") {
    const reviewCount =
      Number.isInteger(place.review_count)
        ? ` (${place.review_count})`
        : "";

    rating.textContent =
      `★ ${place.rating}${reviewCount}`;
  } else {
    rating.textContent = "Not rated";
  }

  const distance = document.createElement("span");
  distance.textContent = formatDistance(place.distance_miles);

  const price = document.createElement("span");
  price.textContent =
    formatPriceLevel(place.price_level) ||
    "Price unavailable";

  const availability = document.createElement("span");
  availability.className = "availability-pill";
  availability.textContent = formatOpenStatus(place.open_now);

  const separators = Array.from(
    { length: 3 },
    () => {
      const separator = document.createElement("span");
      separator.setAttribute("aria-hidden", "true");
      separator.textContent = "·";
      return separator;
    }
  );

  meta.append(
    rating,
    separators[0],
    distance,
    separators[1],
    price,
    separators[2],
    availability
  );

  headingCopy.append(name, meta);

  const saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.className = "save-place-button";
  saveButton.dataset.placeId = place.id;
  saveButton.setAttribute(
    "aria-label",
    `Save ${place.name}`
  );
  saveButton.setAttribute(
    "aria-pressed",
    "false"
  );
  saveButton.setAttribute(
    "data-place-save-button",
    ""
  );

  const saveIcon = document.createElement("span");
  saveIcon.setAttribute("aria-hidden", "true");
  saveIcon.setAttribute("data-lucide", "heart");

  saveButton.append(saveIcon);
  heading.append(headingCopy, saveButton);

  const description = document.createElement("p");
  description.className = "recommendation-description";
  description.textContent = place.description;

  const tag = document.createElement("span");
  tag.className = "recommendation-tag";
  tag.textContent =
    place.tags?.[0] || place.category;

  copy.append(heading, description, tag);

  const actions = document.createElement("div");
  actions.className = "recommendation-actions";

  actions.append(
    createPlaceAction({
      iconName: "navigation",
      label: "Directions",
      ariaLabel: `Get directions to ${place.name}`,
      url: buildDirectionsUrl(place),
    }),
    createPlaceAction({
      iconName: "phone",
      label: "Call",
      ariaLabel: `Call ${place.name}`,
      url: buildPhoneUrl(place.phone),
    }),
    createPlaceAction({
      iconName: "globe-2",
      label: "Website",
      ariaLabel: `Visit ${place.name} website`,
      url: buildWebsiteUrl(place.website),
    })
  );

  card.append(image, copy, actions);

  return card;
};

const createInspectorResult = (place, index) => {
  const result = document.createElement("button");

  result.type = "button";
  result.className = "inspector-result-item";
  result.dataset.placeResult = place.id;

  if (index === 0) {
    result.classList.add("inspector-result-item--active");
  }

  const rank = document.createElement("span");
  rank.className = "inspector-result-rank";
  rank.textContent = String(index + 1);

  const copy = document.createElement("span");
  copy.className = "inspector-result-copy";

  const name = document.createElement("span");
  name.className = "inspector-result-name";
  name.textContent = place.name;

  const meta = document.createElement("span");
  meta.className = "inspector-result-meta";
  meta.textContent = [
    formatRating(place.rating),
    formatDistance(place.distance_miles),
    formatPriceLevel(place.price_level) || "Price unavailable",
  ].join(" · ");

  copy.append(name, meta);
  result.append(rank, copy);

  return result;
};

const createSavedPlaceCard = (place, index) => {
  const card = createRecommendationCard(
    place,
    index
  );

  card.classList.remove(
    "recommendation-card--selected"
  );

  card.removeAttribute(
    "data-recommendation-card"
  );

  card.removeAttribute("tabindex");

  return card;
};

const getSavedPlaces = () => {
  const savedPlaceIds = loadSavedPlaceIds();
  const records = loadSavedPlaceRecords();

  return Array.from(savedPlaceIds)
    .map((placeId, index) => {
      const record =
        records[placeId] || PLACES[placeId];

      return record
        ? normalizePlaceForDashboard(
            record,
            index
          )
        : null;
    })
    .filter(Boolean);
};

const renderSavedPlacesView = () => {
  const list = document.querySelector(
    SELECTORS.savedPlacesList
  );

  const emptyState = document.querySelector(
    SELECTORS.savedPlacesEmpty
  );

  if (!list || !emptyState) {
    return;
  }

  const places = getSavedPlaces();

  list.replaceChildren(
    ...places.map(createSavedPlaceCard)
  );

  list.hidden = places.length === 0;
  emptyState.hidden = places.length > 0;

  places.forEach((place) => {
    updateSavedPlaceButtons(place.id);
  });

  hydrateDashboardIcons();
};

const createDiscoveryIcon = (iconName) => {
  const icon = document.createElement("span");

  icon.setAttribute("aria-hidden", "true");
  icon.setAttribute("data-lucide", iconName);

  return icon;
};

const createDiscoveryMood = (mood) => {
  const button = document.createElement("button");

  button.type = "button";
  button.className =
    `discovery-mood discovery-mood--${mood.tone}`;
  button.dataset.discoveryQuery = mood.query;

  button.setAttribute(
    "aria-label",
    `${mood.title}: ${mood.description}`
  );

  const previewPlace =
    discoveryMoodPreviews.get(mood.id);

  const primaryPhoto = Array.isArray(
    previewPlace?.photos
  )
    ? previewPlace.photos[0]
    : null;

  const photoUrl = buildPlacePhotoUrl(
    primaryPhoto,
    800
  );

  if (photoUrl) {
    const image = document.createElement("img");

    image.className = "discovery-mood-photo";
    image.src = photoUrl;
    image.alt = "";
    image.loading = "lazy";
    image.decoding = "async";

    image.addEventListener("error", () => {
      image.remove();

      button.classList.remove(
        "discovery-mood--has-photo"
      );
    });

    button.classList.add(
      "discovery-mood--has-photo"
    );

    button.append(image);
  }

  const overlay = document.createElement("span");
  overlay.className = "discovery-mood-overlay";
  overlay.setAttribute("aria-hidden", "true");

  const iconShell = document.createElement("span");
  iconShell.className = "discovery-mood-icon";
  iconShell.setAttribute("aria-hidden", "true");

  iconShell.append(
    createDiscoveryIcon(mood.icon)
  );

  const title = document.createElement("strong");
  title.className = "discovery-mood-title";
  title.textContent = mood.title;

  button.append(
    overlay,
    iconShell,
    title
  );

  return button;
};

const createDiscoveryTile = (place) => {
  const button = document.createElement("button");

  button.type = "button";
  button.className = "discovery-tile";
  button.dataset.discoveryQuery =
    place.discovery_query ||
    `Tell me about ${place.name}`;

  button.setAttribute(
    "aria-label",
    `Explore ${place.name}`
  );

  const visual = document.createElement("span");
  visual.className = "discovery-tile-visual";

  const primaryPhoto = Array.isArray(place.photos)
    ? place.photos[0]
    : null;

  const photoUrl = buildPlacePhotoUrl(
    primaryPhoto,
    800
  );

  if (photoUrl) {
    const image = document.createElement("img");

    image.className = "discovery-tile-photo";
    image.src = photoUrl;
    image.alt = `${place.name} location`;
    image.loading = "lazy";
    image.decoding = "async";

    image.addEventListener("error", () => {
      image.remove();

      visual.classList.remove(
        "discovery-tile-visual--has-photo"
      );
    });

    visual.classList.add(
      "discovery-tile-visual--has-photo"
    );

    visual.append(image);

    const attributionNames =
      getPhotoAttributionNames(primaryPhoto);

    if (attributionNames.length > 0) {
      const attribution = document.createElement(
        "span"
      );

      attribution.className =
        "discovery-photo-attribution";

      attribution.textContent =
        `Photo: ${attributionNames.join(", ")}`;

      visual.append(attribution);
    }
  }

  const fallbackIcon =
    document.createElement("span");

  fallbackIcon.className =
    "discovery-tile-icon";

  fallbackIcon.append(
    createDiscoveryIcon("map-pin")
  );

  visual.append(fallbackIcon);

  const content = document.createElement("span");
  content.className = "discovery-tile-content";

  const title = document.createElement("strong");
  title.textContent = place.name;

  const metadata = document.createElement("span");

  metadata.textContent = [
    place.category,
    Number.isFinite(place.rating)
      ? `${place.rating} ★`
      : null,
    Number.isFinite(place.distance_miles)
      ? `${place.distance_miles.toFixed(1)} mi`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");

  content.append(title, metadata);

  const arrow = createDiscoveryIcon(
    "arrow-up-right"
  );

  arrow.classList.add(
    "discovery-tile-arrow"
  );

  button.append(visual, content, arrow);

  return button;
};

const createDiscoveryCollection = (
  collection
) => {
  const section = document.createElement("section");

  section.className = "discovery-collection";
  section.setAttribute(
    "aria-labelledby",
    `discovery-${collection.id}-title`
  );

  const heading = document.createElement("header");
  heading.className = "discovery-section-heading";

  const headingCopy = document.createElement("div");

  const title = document.createElement("h2");
  title.id = `discovery-${collection.id}-title`;
  title.textContent = collection.title;

  const description = document.createElement("p");
  description.className =
    "discovery-section-description";
  description.textContent =
    collection.description || "";

  headingCopy.append(
    title,
    description
  );

  heading.append(headingCopy);

  const track = document.createElement("div");
  track.className = "discovery-track";

  track.replaceChildren(
    ...collection.places.map(
      createDiscoveryTile
    )
  );

  section.append(heading, track);

  return section;
};

const updateDiscoveryLocation = () => {
  const location = document.querySelector(
    SELECTORS.discoveryLocation
  );

  if (!location) {
    return;
  }

  const locationName =
    selectedLocation.label
      .split(",")[0]
      ?.trim() || "places nearby";

  location.textContent = locationName;
};

const setDiscoveryStatus = ({
  title,
  message,
  isError = false,
  hidden = false,
}) => {
  const status = document.querySelector(
    SELECTORS.discoveryStatus
  );

  const titleElement = document.querySelector(
    SELECTORS.discoveryStatusTitle
  );

  const messageElement = document.querySelector(
    SELECTORS.discoveryStatusMessage
  );

  if (
    !status ||
    !titleElement ||
    !messageElement
  ) {
    return;
  }

  titleElement.textContent = title;
  messageElement.textContent = message;

  status.classList.toggle(
    "discovery-loading-state--error",
    isError
  );

  status.hidden = hidden;
};

const fetchDiscoveryCollections = async ({
  signal,
} = {}) => {
  const response = await fetch(
    "/api/v1/discovery",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      signal,
      body: JSON.stringify({
        location: {
          latitude: selectedLocation.latitude,
          longitude: selectedLocation.longitude,
        },
      }),
    }
  );

  let data = {};

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(
      data.error?.message ||
        "CityGuide could not load local collections."
    );
  }

  return data;
};

const renderDiscoveryHub = async ({
  force = false,
} = {}) => {
  const moodGrid = document.querySelector(
    SELECTORS.discoveryMoodGrid
  );

  const collections = document.querySelector(
    SELECTORS.discoveryCollections
  );

  if (!moodGrid || !collections) {
    return;
  }

  moodGrid.replaceChildren(
    ...DISCOVERY_MOODS.map(
      createDiscoveryMood
    )
  );

  updateDiscoveryLocation();
  hydrateDashboardIcons();

  const locationKey = [
    selectedLocation.latitude.toFixed(5),
    selectedLocation.longitude.toFixed(5),
  ].join(":");

  if (
    !force &&
    discoveryCacheKey === locationKey &&
    discoverySections.length > 0
  ) {
    collections.replaceChildren(
      ...discoverySections.map(
        createDiscoveryCollection
      )
    );

    collections.hidden = false;

    setDiscoveryStatus({
      title: "",
      message: "",
      hidden: true,
    });

    hydrateDashboardIcons();
    return;
  }

  const requestId = ++discoveryRequestId;

  collections.hidden = true;

  setDiscoveryStatus({
    title: "Finding places near you",
    message:
      "CityGuide is preparing local collections.",
  });

  try {
    const response =
      await fetchDiscoveryCollections();

    if (requestId !== discoveryRequestId) {
      return;
    }

    discoveryCacheKey = locationKey;

    discoveryMoodPreviews = new Map(
      Array.isArray(response.moods)
        ? response.moods
            .filter(
              (mood) =>
                typeof mood?.id === "string" &&
                mood.place
            )
            .map((mood) => [
              mood.id,
              mood.place,
            ])
        : []
    );

    discoverySections = Array.isArray(
      response.sections
    )
      ? response.sections.filter(
          (section) =>
            Array.isArray(section.places) &&
            section.places.length > 0
        )
      : [];

    if (discoverySections.length === 0) {
      setDiscoveryStatus({
        title: "No collections found",
        message:
          "Try another location or begin with one of the mood options above.",
      });

      return;
    }

    moodGrid.replaceChildren(
      ...DISCOVERY_MOODS.map(
        createDiscoveryMood
      )
    );

    collections.replaceChildren(
      ...discoverySections.map(
        createDiscoveryCollection
      )
    );

    collections.hidden = false;

    setDiscoveryStatus({
      title: "",
      message: "",
      hidden: true,
    });

    hydrateDashboardIcons();
  } catch (error) {
    if (requestId !== discoveryRequestId) {
      return;
    }

    console.error(
      "CityGuide discovery failed:",
      error
    );

    setDiscoveryStatus({
      title: "Local collections unavailable",
      message:
        error.message ||
        "Try again in a moment.",
      isError: true,
    });
  }
};

const launchDiscoverySearch = (query) => {
  const searchInput = document.querySelector(
    SELECTORS.searchInput
  );

  const searchForm = document.querySelector(
    SELECTORS.searchForm
  );

  if (!searchInput || !searchForm || !query) {
    return;
  }

  setDashboardView("explore");

  searchInput.value = query;

  searchInput.dispatchEvent(
    new Event("input", {
      bubbles: true,
    })
  );

  searchInput.focus();
  searchForm.requestSubmit();
};

const initializeDiscoveryHub = () => {
  const categoriesView = document.querySelector(
    '[data-dashboard-view="categories"]'
  );

  if (!categoriesView) {
    return;
  }

  categoriesView.addEventListener(
    "click",
    (event) => {
      const trigger = event.target.closest(
        SELECTORS.discoveryQuery
      );

      if (!trigger) {
        return;
      }

      launchDiscoverySearch(
        trigger.dataset.discoveryQuery
      );
    }
  );
};

const setDashboardView = (viewName) => {
  const supportedViews = new Set([
    "explore",
    "saved",
    "categories",
  ]);

  activeDashboardView = supportedViews.has(viewName)
    ? viewName
    : "explore";

  const isContentView =
    activeDashboardView !== "explore";

  document
    .querySelectorAll(SELECTORS.dashboardView)
    .forEach((view) => {
      view.hidden =
        view.dataset.dashboardView !==
        activeDashboardView;
    });

  document
    .querySelectorAll(
      SELECTORS.dashboardNavigation
    )
    .forEach((link) => {
      const isActive =
        link.dataset.dashboardNavigation ===
        activeDashboardView;

      link.classList.toggle(
        "sidebar-link--active",
        isActive
      );

      if (isActive) {
        link.setAttribute(
          "aria-current",
          "page"
        );
      } else {
        link.removeAttribute("aria-current");
      }
    });

  document
    .querySelector(SELECTORS.sidebarShell)
    ?.classList.toggle(
      "dashboard-shell--saved-view",
      isContentView
    );

  if (activeDashboardView === "saved") {
    renderSavedPlacesView();
  }

  if (activeDashboardView === "categories") {
    void renderDiscoveryHub();
  }

  hydrateDashboardIcons();
};

const initializeDashboardNavigation = () => {
  document
    .querySelectorAll(
      SELECTORS.dashboardNavigation
    )
    .forEach((link) => {
      link.addEventListener(
        "click",
        (event) => {
          event.preventDefault();

          setDashboardView(
            link.dataset.dashboardNavigation
          );
        }
      );
    });

  document
    .querySelector(
      SELECTORS.savedPlacesExplore
    )
    ?.addEventListener("click", () => {
      setDashboardView("explore");

      document
        .querySelector(SELECTORS.searchInput)
        ?.focus();
    });
};

const renderRecommendationCards = (places) => {
  const recommendationList = document.querySelector(
    SELECTORS.recommendationList
  );

  if (!recommendationList) {
    return;
  }

  recommendationList.replaceChildren(
    ...places.map(createRecommendationCard)
  );

  places.forEach((place) => {
    updateSavedPlaceButtons(place.id);
  });

  initializeRecommendationCards();
  hydrateDashboardIcons();
};

const renderInspectorResults = (places) => {
  const resultsList = document.querySelector(
    SELECTORS.inspectorResultsList
  );

  if (!resultsList) {
    return;
  }

  resultsList.replaceChildren(
    ...places.map(createInspectorResult)
  );

  initializeInspectorResults();
};

const renderMapMarkers = async (places) => {
  const map = await initializeInteractiveMap();

  if (!map) {
    return;
  }

  clearMapMarkers();

  const validPlaces = places
    .filter((place) => getPlaceCoordinates(place))
    .filter((place) => {
      const distance = Number(place.distance_miles);

      return (
        !Number.isFinite(distance) ||
        distance <= 25
      );
    });

  if (validPlaces.length === 0) {
    return;
  }

  const { AdvancedMarkerElement, PinElement } =
    await window.google.maps.importLibrary(
      "marker"
    );

  const bounds =
    new window.google.maps.LatLngBounds();

  validPlaces.forEach((place, index) => {
    const position = getPlaceCoordinates(place);

    const pin = new PinElement({
      glyph: String(index + 1),
      background: "#16252d",
      borderColor: "#d88a22",
      glyphColor: "#ffffff",
      scale: 1.05,
    });

    const marker = new AdvancedMarkerElement({
      map,
      position,
      title: place.name,
      content: pin.element,
      gmpClickable: true,
    });

    marker.addListener("click", () => {
      selectPlace(place.id);
    });

    placeMapMarkers.set(place.id, {
      marker,
      pin,
      position,
    });

    bounds.extend(position);
  });

  if (validPlaces.length === 1) {
    map.setCenter(
      getPlaceCoordinates(validPlaces[0])
    );
    map.setZoom(15);
  } else {
    map.fitBounds(bounds, 48);
  }
};

const initializeFilterChips = () => {
  const filterChips = document.querySelectorAll(
    SELECTORS.filterChip
  );

  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((currentChip) => {
        currentChip.classList.remove("filter-chip--active");
        currentChip.setAttribute("aria-pressed", "false");
      });

      chip.classList.add("filter-chip--active");
      chip.setAttribute("aria-pressed", "true");
    });
  });
};

const createPlaceGalleryThumbnail = (
  place,
  photo,
  index
) => {
  const thumbnail = document.createElement("button");

  thumbnail.type = "button";
  thumbnail.className = "place-gallery-thumbnail";
  thumbnail.setAttribute(
    "aria-label",
    `View photo ${index + 1} of ${place.name}`
  );

  const photoUrl = buildPlacePhotoUrl(photo, 400);

  if (!photoUrl) {
    thumbnail.disabled = true;
    return thumbnail;
  }

  const image = document.createElement("img");

  image.src = photoUrl;
  image.alt = "";
  image.loading = "lazy";
  image.decoding = "async";

  image.addEventListener("error", () => {
    const wasActive = thumbnail.classList.contains(
      "place-gallery-thumbnail--active"
    );

    thumbnail.remove();

    if (wasActive) {
      const nextThumbnail = document.querySelector(
        ".place-gallery-thumbnail"
      );

      nextThumbnail?.click();
    }
  });

  thumbnail.append(image);

  thumbnail.addEventListener("click", () => {
    updateSelectedPlacePhoto(
      place,
      photo,
      index
    );
  });

  return thumbnail;
};

const updateSelectedPlacePhoto = (
  place,
  photo,
  activeIndex = 0
) => {
  const requestId = ++latestHeroPhotoRequestId;
  const hero = document.querySelector(
    SELECTORS.placeHero
  );
  const heroPhoto = hero?.querySelector(
    "[data-place-hero-photo]"
  );
  const attribution = document.querySelector(
    SELECTORS.placePhotoAttribution
  );
  const gallery = document.querySelector(
    SELECTORS.placeGallery
  );

  if (!hero || !heroPhoto || !attribution) {
    return;
  }

  const photoUrl = buildPlacePhotoUrl(photo, 1600);

  gallery
    ?.querySelectorAll(".place-gallery-thumbnail")
    .forEach((thumbnail, index) => {
      thumbnail.classList.toggle(
        "place-gallery-thumbnail--active",
        index === activeIndex
      );
    });

  if (!photoUrl) {
    if (requestId !== latestHeroPhotoRequestId) {
      return;
    }

    heroPhoto.hidden = true;
    heroPhoto.removeAttribute("src");
    heroPhoto.alt = "";
    hero.classList.remove("place-hero--has-photo");
    attribution.hidden = true;
    attribution.textContent = "";
    return;
  }

  heroPhoto.hidden = true;
  heroPhoto.alt = `${place.name} location`;
  heroPhoto.src = photoUrl;

  const attributionNames =
    getPhotoAttributionNames(photo);

  if (attributionNames.length > 0) {
    attribution.textContent =
      `Photo: ${attributionNames.join(", ")}`;
    attribution.hidden = false;
  } else {
    attribution.textContent = "";
    attribution.hidden = true;
  }

  heroPhoto.onload = () => {
    if (requestId !== latestHeroPhotoRequestId) {
      return;
    }

    heroPhoto.hidden = false;
    hero.classList.add("place-hero--has-photo");
  };

  heroPhoto.onerror = () => {
    if (requestId !== latestHeroPhotoRequestId) {
      return;
    }

    heroPhoto.hidden = true;
    heroPhoto.removeAttribute("src");
    heroPhoto.alt = "";
    hero.classList.remove("place-hero--has-photo");
    attribution.hidden = true;
    attribution.textContent = "";
  };
};

const renderSelectedPlacePhotos = (place) => {
  const gallery = document.querySelector(
    SELECTORS.placeGallery
  );

  if (!gallery) {
    return;
  }

  const photos = place.photos
    .filter(
      (photo) =>
        typeof photo?.name === "string" &&
        photo.name.trim().length > 0
    )
    .slice(0, 5);

  gallery.replaceChildren(
    ...photos.map((photo, index) =>
      createPlaceGalleryThumbnail(
        place,
        photo,
        index
      )
    )
  );

  gallery.hidden = photos.length === 0;

  updateSelectedPlacePhoto(
    place,
    photos[0] || null,
    0
  );
};

const updatePlaceDetails = (placeId) => {
  const place = PLACES[placeId];

  if (!place) {
    return;
  }

  document.querySelector("[data-place-name]").textContent =
    place.name;

  const ratingLabel =
    typeof place.rating === "number"
      ? Number.isInteger(place.review_count)
        ? `${place.rating} (${place.review_count} reviews)`
        : String(place.rating)
      : "Not rated";
  const distanceLabel =
    place.distance ||
    formatDistance(place.distance_miles);
  const priceLabel =
    place.price ||
    formatPriceLevel(place.price_level) ||
    "Price unavailable";
  const statusLabel =
    place.status ||
    formatOpenStatus(place.open_now);

  document
    .querySelectorAll(
      ".place-details-card [data-place-save-button]"
    )
    .forEach((button) => {
      button.dataset.placeId = place.id;
      button.disabled = false;
    });

  updateSavedPlaceButtons(place.id);

  document.querySelector("[data-place-rating]").textContent =
    ratingLabel;
  document.querySelector("[data-place-distance]").textContent =
    distanceLabel;
  document.querySelector("[data-place-price]").textContent =
    priceLabel;
  document.querySelector("[data-place-status]").textContent =
    statusLabel;
  document.querySelector("[data-place-address]").textContent =
    place.address || "Address unavailable";
  document.querySelector("[data-place-hours]").textContent =
    place.hours || "Hours unavailable";

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeDirectionsAction
    ),
    {
      url: buildDirectionsUrl(place),
      label: `Get directions to ${place.name}`,
    }
  );

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeCallAction
    ),
    {
      url: buildPhoneUrl(place.phone),
      label: `Call ${place.name}`,
      openInNewTab: false,
    }
  );

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeWebsiteAction
    ),
    {
      url: buildWebsiteUrl(place.website),
      label: `Visit ${place.name} website`,
    }
  );

  const hero = document.querySelector(
    SELECTORS.placeHero
  );

  if (hero) {
    hero.classList.remove(
      "place-hero--one",
      "place-hero--two",
      "place-hero--three"
    );
    hero.classList.add(place.heroClass);
  }

  renderSelectedPlacePhotos(place);

  const reasons = document.querySelector("[data-place-reasons]");

  reasons.replaceChildren(
    ...(place.reasons || []).map((reason) => {
      const listItem = document.createElement("li");
      const icon = document.createElement("span");
      const text = document.createTextNode(reason);

      icon.setAttribute("aria-hidden", "true");
      icon.setAttribute("data-lucide", "check");

      listItem.append(icon, text);

      return listItem;
    })
  );

  hydrateDashboardIcons();
};

const clearSelectedPlaceDetails = () => {
  latestHeroPhotoRequestId += 1;

  const name = document.querySelector("[data-place-name]");
  const rating = document.querySelector("[data-place-rating]");
  const distance = document.querySelector("[data-place-distance]");
  const price = document.querySelector("[data-place-price]");
  const status = document.querySelector("[data-place-status]");
  const address = document.querySelector("[data-place-address]");
  const hours = document.querySelector("[data-place-hours]");
  const reasons = document.querySelector("[data-place-reasons]");
  const hero = document.querySelector(
    SELECTORS.placeHero
  );
  const heroPhoto = hero?.querySelector(
    "[data-place-hero-photo]"
  );
  const gallery = document.querySelector(
    SELECTORS.placeGallery
  );
  const attribution = document.querySelector(
    SELECTORS.placePhotoAttribution
  );

  if (name) {
    name.textContent = "No place selected";
  }

  if (rating) {
    rating.textContent = "Rating unavailable";
  }

  if (distance) {
    distance.textContent = "Distance unavailable";
  }

  if (price) {
    price.textContent = "Price unavailable";
  }

  if (status) {
    status.textContent = "Unavailable";
  }

  if (address) {
    address.textContent = "Address unavailable";
  }

  if (hours) {
    hours.textContent = "Hours unavailable";
  }

  if (reasons) {
    reasons.replaceChildren();
  }

  document
    .querySelectorAll(
      ".place-details-card [data-place-save-button]"
    )
    .forEach((button) => {
      delete button.dataset.placeId;
      button.disabled = true;
      button.classList.remove(
        "place-save-control--saved"
      );
      button.setAttribute(
        "aria-pressed",
        "false"
      );
      button.setAttribute(
        "aria-label",
        "Save selected place"
      );

      const label = button.querySelector(
        "[data-place-save-label]"
      );

      if (label) {
        label.textContent = "Save";
      }
    });

  if (hero && heroPhoto) {
    hero.classList.remove("place-hero--has-photo");
    heroPhoto.hidden = true;
    heroPhoto.removeAttribute("src");
    heroPhoto.alt = "";
  }

  if (gallery) {
    gallery.replaceChildren();
    gallery.hidden = true;
  }

  if (attribution) {
    attribution.textContent = "";
    attribution.hidden = true;
  }

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeDirectionsAction
    ),
    {
      url: null,
      label: "Directions unavailable",
    }
  );

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeCallAction
    ),
    {
      url: null,
      label: "Phone number unavailable",
      openInNewTab: false,
    }
  );

  updatePlaceAction(
    document.querySelector(
      SELECTORS.placeWebsiteAction
    ),
    {
      url: null,
      label: "Website unavailable",
    }
  );
};

const selectPlace = (placeId) => {
  document
    .querySelectorAll(SELECTORS.recommendationCard)
    .forEach((card) => {
      card.classList.toggle(
        "recommendation-card--selected",
        card.dataset.placeId === placeId
      );
    });

  document
    .querySelectorAll(SELECTORS.placeResult)
    .forEach((result) => {
      result.classList.toggle(
        "inspector-result-item--active",
        result.dataset.placeResult === placeId
      );
    });

  updateSelectedMapMarker(placeId);

  const selectedMarker =
    placeMapMarkers.get(placeId);

  if (selectedMarker && dashboardMap) {
    dashboardMap.panTo(
      selectedMarker.position
    );
  }

  updatePlaceDetails(placeId);
};

const initializeRecommendationCards = () => {
  document
    .querySelectorAll(SELECTORS.recommendationCard)
    .forEach((card) => {
      card.addEventListener("click", (event) => {
        if (event.target.closest("button, a")) {
          return;
        }

        selectPlace(card.dataset.placeId);
      });

      card.addEventListener("keydown", (event) => {
        if (event.target.closest("button, a, input, select, textarea")) {
          return;
        }

        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }

        event.preventDefault();
        selectPlace(card.dataset.placeId);
      });
    });
};

const activateInspectorTab = (tabName) => {
  document
    .querySelectorAll(SELECTORS.inspectorTab)
    .forEach((tab) => {
      const isActive = tab.dataset.inspectorTab === tabName;

      tab.classList.toggle("inspector-tab--active", isActive);
      tab.setAttribute("aria-selected", String(isActive));
      tab.tabIndex = isActive ? 0 : -1;
    });

  document
    .querySelectorAll(SELECTORS.inspectorPanel)
    .forEach((panel) => {
      panel.hidden = panel.dataset.inspectorPanel !== tabName;
    });
};

const initializeInspectorTabs = () => {
  const tabs = Array.from(
    document.querySelectorAll(
      SELECTORS.inspectorTab
    )
  );

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => {
      activateInspectorTab(
        tab.dataset.inspectorTab
      );
    });

    tab.addEventListener("keydown", (event) => {
      if (
        event.key !== "ArrowLeft" &&
        event.key !== "ArrowRight" &&
        event.key !== "Home" &&
        event.key !== "End"
      ) {
        return;
      }

      event.preventDefault();

      let nextIndex = index;

      if (event.key === "ArrowRight") {
        nextIndex = (index + 1) % tabs.length;
      }

      if (event.key === "ArrowLeft") {
        nextIndex =
          (index - 1 + tabs.length) %
          tabs.length;
      }

      if (event.key === "Home") {
        nextIndex = 0;
      }

      if (event.key === "End") {
        nextIndex = tabs.length - 1;
      }

      const nextTab = tabs[nextIndex];

      activateInspectorTab(
        nextTab.dataset.inspectorTab
      );
      nextTab.focus();
    });
  });
};

const initializeInspectorResults = () => {
  document
    .querySelectorAll(SELECTORS.placeResult)
    .forEach((result) => {
      result.addEventListener("click", () => {
        selectPlace(result.dataset.placeResult);
        activateInspectorTab("map");
      });
    });
};

const initializeSidebarToggle = () => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const toggle = document.querySelector(
    SELECTORS.sidebarToggle
  );
  const icon = document.querySelector(
    SELECTORS.sidebarToggleIcon
  );

  if (!shell || !toggle || !icon) {
    return;
  }

  const syncSidebarToggleState = () => {
    const isCollapsed = shell.classList.contains(
      "dashboard-shell--sidebar-collapsed"
    );

    toggle.setAttribute(
      "aria-label",
      isCollapsed
        ? "Expand sidebar"
        : "Collapse sidebar"
    );

    toggle.setAttribute(
      "aria-expanded",
      String(!isCollapsed)
    );

    icon.setAttribute(
      "data-lucide",
      isCollapsed
        ? "chevrons-right"
        : "chevrons-left"
    );

    hydrateDashboardIcons();
  };

  toggle.addEventListener("click", () => {
    shell.classList.toggle(
      "dashboard-shell--sidebar-collapsed"
    );

    syncSidebarToggleState();
  });

  syncSidebarToggleState();
};

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

const getFocusableElements = (container) =>
  Array.from(
    container.querySelectorAll(FOCUSABLE_SELECTOR)
  ).filter(
    (element) =>
      !element.closest(
        "[hidden], [aria-hidden='true'], [inert]"
      )
  );

const trapFocusWithin = (event, container) => {
  if (event.key !== "Tab") {
    return;
  }

  const focusableElements =
    getFocusableElements(container);

  if (focusableElements.length === 0) {
    event.preventDefault();
    return;
  }

  const firstElement = focusableElements[0];
  const lastElement =
    focusableElements[
      focusableElements.length - 1
    ];

  if (
    event.shiftKey &&
    document.activeElement === firstElement
  ) {
    event.preventDefault();
    lastElement.focus();
    return;
  }

  if (
    !event.shiftKey &&
    document.activeElement === lastElement
  ) {
    event.preventDefault();
    firstElement.focus();
  }
};

const setDrawerAccessibility = (
  drawer,
  isAvailable
) => {
  drawer.inert = !isAvailable;

  if (isAvailable) {
    drawer.removeAttribute("aria-hidden");
    return;
  }

  drawer.setAttribute("aria-hidden", "true");
};

const syncMobileDrawerAccessibility = () => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const sidebar = document.querySelector(
    SELECTORS.dashboardSidebar
  );
  const inspector = document.querySelector(
    SELECTORS.dashboardInspector
  );

  if (!shell || !sidebar || !inspector) {
    return;
  }

  const sidebarIsMobile =
    window.innerWidth <= 760;
  const inspectorIsMobile =
    window.innerWidth <= 900;

  setDrawerAccessibility(
    sidebar,
    !sidebarIsMobile ||
      shell.classList.contains(
        "dashboard-shell--mobile-sidebar-open"
      )
  );

  setDrawerAccessibility(
    inspector,
    !inspectorIsMobile ||
      shell.classList.contains(
        "dashboard-shell--mobile-inspector-open"
      )
  );
};

const updateBodyScrollLock = () => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );

  if (!shell) {
    return;
  }

  const hasOpenOverlay =
    shell.classList.contains(
      "dashboard-shell--mobile-sidebar-open"
    ) ||
    shell.classList.contains(
      "dashboard-shell--mobile-inspector-open"
    );

  document.body.style.overflow = hasOpenOverlay
    ? "hidden"
    : "";
};

const setMobileSidebarOpen = (isOpen, restoreFocus = false) => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const sidebar = document.querySelector(
    SELECTORS.dashboardSidebar
  );
  const toggle = document.querySelector(
    SELECTORS.mobileSidebarToggle
  );
  const backdrop = document.querySelector(
    SELECTORS.sidebarBackdrop
  );

  if (!shell || !sidebar || !toggle || !backdrop) {
    return;
  }

  shell.classList.toggle(
    "dashboard-shell--mobile-sidebar-open",
    isOpen
  );

  toggle.setAttribute(
    "aria-expanded",
    String(isOpen)
  );

  toggle.setAttribute(
    "aria-label",
    isOpen
      ? "Close navigation"
      : "Open navigation"
  );

  backdrop.hidden = !isOpen;

  syncMobileDrawerAccessibility();

  if (isOpen) {
    const firstFocusable =
      getFocusableElements(sidebar)[0];

    firstFocusable?.focus();
  } else if (restoreFocus) {
    toggle.focus();
  }

  updateBodyScrollLock();
};

const setMobileInspectorOpen = (isOpen, restoreFocus = false) => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const inspector = document.querySelector(
    SELECTORS.dashboardInspector
  );
  const toggle = document.querySelector(
    SELECTORS.mobileInspectorToggle
  );
  const backdrop = document.querySelector(
    SELECTORS.inspectorBackdrop
  );
  const closeButton = document.querySelector(
    SELECTORS.mobileInspectorClose
  );

  if (!shell || !inspector || !toggle || !backdrop) {
    return;
  }

  if (isOpen) {
    setMobileSidebarOpen(false);
  }

  shell.classList.toggle(
    "dashboard-shell--mobile-inspector-open",
    isOpen
  );

  toggle.setAttribute(
    "aria-expanded",
    String(isOpen)
  );

  toggle.setAttribute(
    "aria-label",
    isOpen
      ? "Close map and place details"
      : "Open map and place details"
  );

  backdrop.hidden = !isOpen;

  syncMobileDrawerAccessibility();

  if (isOpen) {
    closeButton?.focus();
  } else if (restoreFocus) {
    toggle.focus();
  }

  updateBodyScrollLock();
};

const initializeMobileSidebar = () => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const drawer = document.querySelector(
    SELECTORS.dashboardSidebar
  );
  const toggle = document.querySelector(
    SELECTORS.mobileSidebarToggle
  );
  const backdrop = document.querySelector(
    SELECTORS.sidebarBackdrop
  );

  if (!shell || !drawer || !toggle || !backdrop) {
    return;
  }

  toggle.addEventListener("click", () => {
    const isOpen = shell.classList.contains(
      "dashboard-shell--mobile-sidebar-open"
    );

    setMobileSidebarOpen(!isOpen);
  });

  backdrop.addEventListener("click", () => {
    setMobileSidebarOpen(false, true);
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Tab" &&
      shell.classList.contains(
        "dashboard-shell--mobile-sidebar-open"
      )
    ) {
      trapFocusWithin(event, drawer);
    }

    if (
      event.key === "Escape" &&
      shell.classList.contains(
        "dashboard-shell--mobile-sidebar-open"
      )
    ) {
      setMobileSidebarOpen(false, true);
    }
  });

  window.addEventListener("resize", () => {
    if (
      window.innerWidth > 760 &&
      shell.classList.contains(
        "dashboard-shell--mobile-sidebar-open"
      )
    ) {
      setMobileSidebarOpen(false);
    }

    syncMobileDrawerAccessibility();
  });
};

const initializeMobileInspector = () => {
  const shell = document.querySelector(
    SELECTORS.sidebarShell
  );
  const drawer = document.querySelector(
    SELECTORS.dashboardInspector
  );
  const toggle = document.querySelector(
    SELECTORS.mobileInspectorToggle
  );
  const closeButton = document.querySelector(
    SELECTORS.mobileInspectorClose
  );
  const backdrop = document.querySelector(
    SELECTORS.inspectorBackdrop
  );

  if (
    !shell ||
    !drawer ||
    !toggle ||
    !closeButton ||
    !backdrop
  ) {
    return;
  }

  toggle.addEventListener("click", () => {
    const isOpen = shell.classList.contains(
      "dashboard-shell--mobile-inspector-open"
    );

    setMobileInspectorOpen(!isOpen);
  });

  closeButton.addEventListener("click", () => {
    setMobileInspectorOpen(false, true);
  });

  backdrop.addEventListener("click", () => {
    setMobileInspectorOpen(false, true);
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Tab" &&
      shell.classList.contains(
        "dashboard-shell--mobile-inspector-open"
      )
    ) {
      trapFocusWithin(event, drawer);
    }

    if (
      event.key === "Escape" &&
      shell.classList.contains(
        "dashboard-shell--mobile-inspector-open"
      )
    ) {
      setMobileInspectorOpen(false, true);
    }
  });

  window.addEventListener("resize", () => {
    if (
      window.innerWidth > 900 &&
      shell.classList.contains(
        "dashboard-shell--mobile-inspector-open"
      )
    ) {
      setMobileInspectorOpen(false);
    }

    syncMobileDrawerAccessibility();
  });
};

const searchPlaces = async (query, { signal } = {}) => {
  const response = await fetch("/api/v1/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    signal,
    body: JSON.stringify({
      query,
      location: {
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
      },
    }),
  });

  let data = {};

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const message =
      data.error?.message ||
      "CityGuide could not complete your search.";

    throw new Error(message);
  }

  return data;
};

const continueSearchConversation = async (
  sessionId,
  message,
  { signal } = {}
) => {
  const response = await fetch(
    `/api/v1/search/${encodeURIComponent(sessionId)}/continue`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      signal,
      body: JSON.stringify({
        message,
      }),
    }
  );

  let data = {};

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const error = new Error(
      data.error?.message ||
        "CityGuide could not continue the conversation."
    );

    error.status = response.status;

    throw error;
  }

  return data;
};


const setSearchLoadingState = (isLoading) => {
  const progress = document.querySelector(
    SELECTORS.searchProgress
  );
  const title = document.querySelector(
    SELECTORS.searchProgressTitle
  );
  const progressStatus = document.querySelector(
    SELECTORS.searchProgressStatus
  );

  if (!progress || !title || !progressStatus) {
    return;
  }

  progress.setAttribute(
    "aria-busy",
    String(isLoading)
  );

  title.textContent = isLoading
    ? "Searching local businesses..."
    : "Local business search complete";

  progressStatus.textContent = isLoading
    ? "Searching"
    : "Complete";

  setSearchProgressItemsState(
    isLoading ? "active" : "complete"
  );
};

const setSearchProgressItemsState = (state) => {
  document
    .querySelectorAll(SELECTORS.searchProgressItems)
    .forEach((item) => {
      item.dataset.progressState = state;
    });
};

const setSearchErrorState = () => {
  const progress = document.querySelector(
    SELECTORS.searchProgress
  );
  const title = document.querySelector(
    SELECTORS.searchProgressTitle
  );
  const progressStatus = document.querySelector(
    SELECTORS.searchProgressStatus
  );

  if (!progress || !title || !progressStatus) {
    return;
  }

  progress.setAttribute("aria-busy", "false");
  title.textContent = "Local business search unavailable";
  progressStatus.textContent = "Error";
  setSearchProgressItemsState("error");
};

const hideResultsState = () => {
  const state = document.querySelector(
    SELECTORS.resultsState
  );

  if (state) {
    state.hidden = true;
    state.classList.remove(
      "dashboard-results-state--error"
    );
  }
};

const showResultsState = ({
  title,
  message,
  isError = false,
}) => {
  const state = document.querySelector(
    SELECTORS.resultsState
  );
  const titleElement = document.querySelector(
    SELECTORS.resultsStateTitle
  );
  const messageElement = document.querySelector(
    SELECTORS.resultsStateMessage
  );

  if (!state || !titleElement || !messageElement) {
    return;
  }

  titleElement.textContent = title;
  messageElement.textContent = message;

  state.classList.toggle(
    "dashboard-results-state--error",
    isError
  );

  state.hidden = false;
  hydrateDashboardIcons();
};

const applySearchResults = (places) => {
  const normalizedPlaces =
    updateCurrentPlaces(places);

  renderRecommendationCards(normalizedPlaces);
  renderInspectorResults(normalizedPlaces);

  if (normalizedPlaces.length > 0) {
    void renderMapMarkers(
      normalizedPlaces
    ).then(() => {
      selectPlace(normalizedPlaces[0].id);
    });
  } else {
    clearMapMarkers();
    clearSelectedPlaceDetails();
  }
};

const clearSearchResults = () => {
  applySearchResults([]);
};

const initializeDashboardSearch = () => {
  const form = document.querySelector(
    SELECTORS.searchForm
  );

  const input = document.querySelector(
    SELECTORS.searchInput
  );

  const submitButton = document.querySelector(
    SELECTORS.searchSubmit
  );

  const status = document.querySelector(
    SELECTORS.searchStatus
  );

  if (!form || !input || !submitButton || !status) {
    return;
  }

  const updateSubmitState = () => {
    submitButton.disabled =
      input.value.trim().length === 0;
  };

  input.addEventListener("input", updateSubmitState);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = input.value.trim();

    if (!query) {
      status.textContent =
        "Please enter a search query.";
      updateSubmitState();
      input.focus();
      return;
    }

    const requestId = ++latestSearchRequestId;
    const isFollowUp =
      typeof activeSearchSessionId === "string" &&
      activeSearchSessionId.length > 0;

    appendConversationMessage({
      role: "user",
      text: query,
    });

    const pendingAssistantMessage =
      appendConversationMessage({
        role: "assistant",
        text: isFollowUp
          ? "Reviewing your current results..."
          : "Searching for local places...",
        pending: true,
      });

    input.value = "";

    input.disabled = true;
    submitButton.disabled = true;

    if (isFollowUp) {
      status.textContent =
        "Continuing the current conversation.";
    } else {
      setSearchLoadingState(true);
      hideResultsState();

      status.textContent =
        "Searching for local businesses.";
    }

    let searchFailed = false;

    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      SEARCH_TIMEOUT_MILLISECONDS
    );

    try {
      if (isFollowUp) {
        const continuationResponse =
          await continueSearchConversation(
            activeSearchSessionId,
            query,
            {
              signal: controller.signal,
            }
          );

        if (requestId !== latestSearchRequestId) {
          return;
        }

        updateConversationMessage(
          pendingAssistantMessage,
          continuationResponse.response
        );

        status.textContent =
          "Conversation continued.";

        return;
      }

      const searchResponse = await searchPlaces(query, {
        signal: controller.signal,
      });

      if (requestId !== latestSearchRequestId) {
        return;
      }

      activeSearchSessionId =
        typeof searchResponse.search_id === "string"
          ? searchResponse.search_id
          : null;

      if (searchResponse.results.length === 0) {
        clearSearchResults();

        updateConversationMessage(
          pendingAssistantMessage,
          "I couldn’t find matching places for that request. " +
            "Try changing the wording or broadening your search."
        );

        showResultsState({
          title: "No matching places found",
          message:
            "Try changing your wording, increasing the distance, or removing one preference.",
        });

        status.textContent =
          "Search complete. No matching places found.";

        return;
      }

      status.textContent =
        `Search complete. Found ` +
        `${searchResponse.result_count} results.`;

      applySearchResults(searchResponse.results);

      const assistantResponse =
        typeof searchResponse.assistant_response === "string"
          ? searchResponse.assistant_response.trim()
          : "";

      updateConversationMessage(
        pendingAssistantMessage,
        assistantResponse ||
          buildSearchResultMessage(
            query,
            searchResponse.result_count
          )
      );

      console.log(
        "CityGuide search response:",
        searchResponse
      );
    } catch (error) {
      if (requestId !== latestSearchRequestId) {
        return;
      }

      if (!isFollowUp) {
        clearSearchResults();
      }

      searchFailed = true;

      if (
        isFollowUp &&
        error instanceof Error &&
        error.status === 404
      ) {
        activeSearchSessionId = null;
      }

      const requestTimedOut =
        error instanceof Error &&
        error.name === "AbortError";

      const message = requestTimedOut
        ? "The search took too long. Please try again."
        : error instanceof Error
        ? error.message
        : "CityGuide could not complete your search.";

      status.textContent = message;

      updateConversationMessage(
        pendingAssistantMessage,
        requestTimedOut
          ? isFollowUp
            ? "The follow-up took too long. Please try again."
            : "The local search took too long. Please try again."
          : isFollowUp
          ? "I couldn’t continue this conversation right now. " +
            "Please try again."
          : "I couldn’t load local recommendations right now. " +
            "Please try again."
      );

      if (!isFollowUp) {
        showResultsState({
          title: "We could not complete your search",
          message,
          isError: true,
        });
      }

      console.error("CityGuide search failed:", error);
    } finally {
      window.clearTimeout(timeoutId);

      if (requestId !== latestSearchRequestId) {
        return;
      }

      if (!isFollowUp) {
        if (searchFailed) {
          setSearchErrorState();
        } else {
          setSearchLoadingState(false);
        }
      }
      input.disabled = false;
      updateSubmitState();
      input.focus();
    }
  });

  updateSubmitState();
};

const initializeConversation = () => {
  appendConversationMessage({
    role: "assistant",
    text:
      "Hi! Tell me what kind of place, service, food, or activity " +
      `you are looking for near ${selectedLocation.label}.`,
  });
};

const initializeLocationSelector = () => {
  const selector = document.querySelector(
    SELECTORS.locationSelector
  );

  const panel = document.querySelector(
    SELECTORS.locationPanel
  );

  const autocompleteContainer =
    document.querySelector(
      SELECTORS.locationAutocomplete
    );

  const status = document.querySelector(
    SELECTORS.locationStatus
  );

  const currentLocationButton =
    document.querySelector(
      SELECTORS.currentLocationButton
    );

  if (
    !selector ||
    !panel ||
    !autocompleteContainer ||
    !status ||
    !currentLocationButton
  ) {
    return;
  }

  const setPanelOpen = (isOpen) => {
    panel.hidden = !isOpen;

    selector.setAttribute(
      "aria-expanded",
      String(isOpen)
    );
  };

  selector.addEventListener("click", () => {
    setPanelOpen(panel.hidden);
  });

  document.addEventListener("click", (event) => {
    if (
      panel.hidden ||
      event.target.closest(".location-control")
    ) {
      return;
    }

    setPanelOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || panel.hidden) {
      return;
    }

    setPanelOpen(false);
    selector.focus();
  });

  currentLocationButton.addEventListener(
    "click",
    () => {
      if (!navigator.geolocation) {
        status.textContent =
          "Current-location detection is not supported. " +
          "Choose a location manually instead.";

        return;
      }

      currentLocationButton.disabled = true;
      status.textContent =
        "Finding your current location...";

      navigator.geolocation.getCurrentPosition(
        async ({ coords }) => {
          const latitude = coords.latitude;
          const longitude = coords.longitude;

          try {
            await loadGoogleMapsLibrary();

            const label = await getLocationLabel({
              latitude,
              longitude,
            });

            setSelectedLocation({
              label,
              latitude,
              longitude,
            });

            clearSearchResults();

            status.textContent =
              `Search location changed to ${label}.`;

            appendConversationMessage({
              role: "assistant",
              text:
                `Search location changed to ${label}. ` +
                "Your next search will use this area.",
            });

            setPanelOpen(false);
          } catch (error) {
            const fallbackLabel =
              `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;

            setSelectedLocation({
              label: fallbackLabel,
              latitude,
              longitude,
            });

            clearSearchResults();

            status.textContent =
              "Your current coordinates were found, but the " +
              "location name could not be determined.";

            appendConversationMessage({
              role: "assistant",
              text:
                `Search location changed to ${fallbackLabel}. ` +
                "Your next search will use this area.",
            });

            setPanelOpen(false);

            console.error(
              "CityGuide reverse geocoding failed:",
              error
            );
          } finally {
            currentLocationButton.disabled = false;
          }
        },
        (error) => {
          currentLocationButton.disabled = false;
          status.textContent =
            getGeolocationErrorMessage(error);

          console.error(
            "CityGuide geolocation failed:",
            error
          );
        },
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000,
        }
      );
    }
  );

  void loadGoogleMapsLibrary()
    .then(async () => {
      const { PlaceAutocompleteElement } =
        await window.google.maps.importLibrary(
          "places"
        );

      const autocomplete =
        new PlaceAutocompleteElement();

      autocomplete.placeholder =
        "Search for a city or area";

      autocomplete.addEventListener(
        "gmp-select",
        async ({ placePrediction }) => {
          status.textContent =
            "Updating search location...";

          try {
            const place =
              placePrediction.toPlace();

            await place.fetchFields({
              fields: [
                "displayName",
                "formattedAddress",
                "location",
              ],
            });

            const latitude =
              place.location?.lat();

            const longitude =
              place.location?.lng();

            const label =
              place.formattedAddress ||
              place.displayName;

            setSelectedLocation({
              label,
              latitude,
              longitude,
            });

            status.textContent =
              `Search location changed to ${label}.`;

            appendConversationMessage({
              role: "assistant",
              text:
                `Search location changed to ${label}. ` +
                "Your next search will use this area.",
            });

            clearSearchResults();
            setPanelOpen(false);
          } catch (error) {
            status.textContent =
              "CityGuide could not use that location.";

            console.error(
              "CityGuide location selection failed:",
              error
            );
          }
        }
      );

      autocompleteContainer.replaceChildren(
        autocomplete
      );
    })
    .catch((error) => {
      status.textContent =
        "Location search is temporarily unavailable.";

      console.error(
        "CityGuide location autocomplete failed:",
        error
      );
    });
};

const initializeNewChat = () => {
  const button = document.querySelector(
    SELECTORS.newChatButton
  );

  const conversation = document.querySelector(
    SELECTORS.conversation
  );

  if (!button || !conversation) {
    return;
  }

  button.addEventListener("click", () => {
    setDashboardView("explore");

    activeSearchSessionId = null;
    latestSearchRequestId += 1;

    clearSearchResults();
    conversation.replaceChildren();

    initializeConversation();
    setSearchProgressItemsState("ready");

    const status = document.querySelector(
      SELECTORS.searchStatus
    );

    if (status) {
      status.textContent =
        "Ready for a new local search.";
    }

    resetSearchComposer();

    document
      .querySelector(SELECTORS.searchInput)
      ?.focus();
  });
};

const initializeProfileMenu = () => {
  const menu = document.querySelector(
    SELECTORS.profileMenu
  );

  const trigger = document.querySelector(
    SELECTORS.profileMenuTrigger
  );

  const popover = document.querySelector(
    SELECTORS.profileMenuPopover
  );

  if (!menu || !trigger || !popover) {
    return;
  }

  const setMenuOpen = (isOpen) => {
    trigger.setAttribute(
      "aria-expanded",
      String(isOpen)
    );

    popover.hidden = !isOpen;
  };

  trigger.addEventListener("click", () => {
    const isOpen =
      trigger.getAttribute("aria-expanded") ===
      "true";

    setMenuOpen(!isOpen);
  });

  document.addEventListener("click", (event) => {
    if (
      event.target instanceof Node &&
      !menu.contains(event.target)
    ) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }

    setMenuOpen(false);
    trigger.focus();
  });
};

const initializeDashboard = () => {
  updateLocationLabels();
  initializeLocationSelector();
  initializeConversation();
  initializeProfileMenu();
  setSearchProgressItemsState("ready");
  initializeFilterChips();
  initializeRecommendationCards();
  initializeSavedPlaces();
  initializeDashboardNavigation();
  initializeDiscoveryHub();
  initializeInspectorTabs();
  initializeInspectorResults();
  activateInspectorTab("map");
  initializeSidebarToggle();
  initializeMobileSidebar();
  initializeMobileInspector();
  initializeNewChat();
  initializeDashboardSearch();
  syncMobileDrawerAccessibility();
};

document.addEventListener("DOMContentLoaded", initializeDashboard);

if (typeof window.requestIdleCallback === "function") {
  window.requestIdleCallback(hydrateDashboardIcons);
} else {
  window.setTimeout(hydrateDashboardIcons, 0);
}

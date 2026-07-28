import pytest

from app.extensions import db
from app.models import User


def authenticate_client(client, app):
    with app.app_context():
        user = User(
            email="dashboard@example.com",
            display_name="Dashboard User",
            google_sub="dashboard-google-user",
            avatar_url=None,
        )

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id

    return user_id


@pytest.mark.parametrize(
    ("path", "expected_text"),
    [
        ("/", b"Instead"),
        ("/login", b"Sign in to Instead"),
        ("/terms", b"Terms of Service"),
        ("/privacy", b"Privacy Policy"),
    ],
)
def test_page_routes_return_success(client, path, expected_text):
    response = client.get(path)

    assert response.status_code == 200
    assert expected_text in response.data


def test_unknown_route_returns_not_found(client):
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404


def test_signup_redirects_to_login(client):
    response = client.get(
        "/signup",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


@pytest.mark.parametrize(
    "path",
    [
        "/static/css/styles.css",
        "/static/css/auth.css",
        "/static/css/dashboard.css",
        "/static/css/legal.css",
        "/static/js/app.js",
        "/static/js/auth.js",
        "/static/js/dashboard.js",
        "/static/images/hero_img.jpg",
        "/static/images/instead-logo.svg",
        "/static/images/cityguide-transparent.png",
    ],
)
def test_static_assets_are_served(client, path):
    response = client.get(path)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/login",
        "/privacy",
        "/terms",
    ],
)
def test_pages_use_instead_logo(client, path):
    response = client.get(path)

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert (
        "images/instead-logo.svg"
        in html
    )


def test_authenticated_dashboard_uses_instead_logo(
    client,
    app,
):
    authenticate_client(client, app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert (
        "/static/images/instead-logo.svg"
        in response.get_data(as_text=True)
    )


def test_dashboard_contains_result_filter_controls(
    client,
    app,
):
    authenticate_client(client, app)

    response = client.get("/dashboard")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'data-filter="all"' in html
    assert 'data-filter="budget"' in html
    assert 'data-filter="moderate"' in html
    assert 'data-filter="premium"' in html
    assert 'data-filter="open"' in html
    assert 'data-filter="rated"' in html
    assert 'data-filter="nearby"' in html


def test_dashboard_javascript_implements_result_filters(
    client,
):
    response = client.get("/static/js/dashboard.js")

    assert response.status_code == 200

    javascript = response.get_data(as_text=True)

    assert "const activeResultFilters = new Set()" in javascript
    assert "const FILTER_SETTINGS = Object.freeze" in javascript
    assert "const placeMatchesActiveFilters" in javascript
    assert "const getFilteredSearchPlaces" in javascript
    assert "const renderFilteredSearchResults" in javascript
    assert "const resetResultFilters" in javascript
    assert "No places match these filters" in javascript


def test_dashboard_javascript_sends_filters_to_search_api(
    client,
):
    response = client.get(
        "/static/js/dashboard.js"
    )

    assert response.status_code == 200

    javascript = response.get_data(as_text=True)

    assert "const buildActiveSearchFilters" in javascript
    assert "price_levels" in javascript
    assert "open_now" in javascript
    assert "minimum_rating" in javascript
    assert "max_distance_meters" in javascript
    assert "filters: buildActiveSearchFilters()" in javascript
    assert "refreshSearchWithActiveFilters" in javascript
    assert "void refreshSearchWithActiveFilters()" in javascript


def test_dashboard_javascript_synchronizes_filter_responses_with_chat(
    client,
):
    response = client.get(
        "/static/js/dashboard.js"
    )

    assert response.status_code == 200

    javascript = response.get_data(as_text=True)

    assert "lastAppliedFilterSignature" in javascript
    assert "buildFilterSignature" in javascript
    assert "searchResponse.assistant_response" in javascript
    assert "appendConversationMessage" in javascript


def test_dashboard_javascript_uses_assistant_response(client):
    response = client.get(
        "/static/js/dashboard.js"
    )

    assert response.status_code == 200

    javascript = response.get_data(
        as_text=True
    )

    assert (
        "searchResponse.assistant_response"
        in javascript
    )

    assert (
        "assistantResponse ||"
        in javascript
    )


def test_dashboard_javascript_initializes_profile_menu(
    client,
):
    response = client.get(
        "/static/js/dashboard.js"
    )

    assert response.status_code == 200

    javascript = response.get_data(as_text=True)

    assert "initializeProfileMenu" in javascript
    assert "profileMenuTrigger" in javascript
    assert '"aria-expanded"' in javascript
    assert '"Escape"' in javascript


def test_dashboard_centralizes_selected_location(client, app):
    authenticate_client(client, app)

    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    template_response = client.get(
        "/dashboard"
    )

    assert javascript_response.status_code == 200
    assert template_response.status_code == 200

    javascript = javascript_response.get_data(
        as_text=True
    )

    html = template_response.get_data(
        as_text=True
    )

    assert "const DEFAULT_LOCATION" in javascript

    assert (
        "selectedLocation.latitude"
        in javascript
    )

    assert (
        "selectedLocation.longitude"
        in javascript
    )

    assert (
        "selectedLocation.label"
        in javascript
    )

    assert (
        "data-current-location-label"
        in html
    )


def test_dashboard_supports_manual_location_selection(client, app):
    authenticate_client(client, app)

    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    dashboard_response = client.get(
        "/dashboard"
    )

    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert javascript_response.status_code == 200
    assert dashboard_response.status_code == 200
    assert stylesheet_response.status_code == 200

    javascript = javascript_response.get_data(
        as_text=True
    )

    html = dashboard_response.get_data(
        as_text=True
    )

    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert "PlaceAutocompleteElement" in javascript
    assert '"gmp-select"' in javascript
    assert "setSelectedLocation" in javascript
    assert "data-location-selector" in html
    assert "data-location-panel" in html
    assert "data-location-autocomplete" in html
    assert ".location-panel" in stylesheet
    assert 'aria-expanded="false"' in html

    assert (
        'aria-controls="dashboard-location-panel"'
        in html
    )

    assert 'id="dashboard-location-panel"' in html

    assert (
        'aria-label="Choose a search location"'
        in html
    )

    assert 'role="status"' in html

    assert 'aria-live="polite"' in html


def test_dashboard_supports_current_location_detection(client, app):
    authenticate_client(client, app)

    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    dashboard_response = client.get(
        "/dashboard"
    )

    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert javascript_response.status_code == 200
    assert dashboard_response.status_code == 200
    assert stylesheet_response.status_code == 200

    javascript = javascript_response.get_data(
        as_text=True
    )

    html = dashboard_response.get_data(
        as_text=True
    )

    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert "navigator.geolocation" in javascript

    assert (
        "navigator.geolocation.getCurrentPosition"
        in javascript
    )

    assert '"geocoding"' in javascript

    assert "getLocationLabel" in javascript
    assert "getGeolocationErrorMessage" in javascript
    assert "getAddressComponent" in javascript
    assert '"locality"' in javascript
    assert '"postal_town"' in javascript

    assert (
        '"administrative_area_level_2"'
        in javascript
    )

    assert (
        '"administrative_area_level_1"'
        in javascript
    )

    assert '"short_name"' in javascript
    assert "fallbackLabel" in javascript

    assert (
        "latitude.toFixed(4)"
        in javascript
    )

    assert (
        "longitude.toFixed(4)"
        in javascript
    )

    assert (
        "SEARCH_TIMEOUT_MILLISECONDS = 30000"
        in javascript
    )

    assert (
        "Your next search will use this area."
        in javascript
    )

    assert (
        "data-current-location-button"
        in html
    )

    assert (
        "Use my current location"
        in html
    )

    assert (
        ".current-location-button"
        in stylesheet
    )


def test_dashboard_routes_followups_through_active_session(client, app):
    authenticate_client(client, app)

    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    dashboard_response = client.get(
        "/dashboard"
    )

    assert javascript_response.status_code == 200
    assert dashboard_response.status_code == 200

    javascript = javascript_response.get_data(
        as_text=True
    )

    html = dashboard_response.get_data(
        as_text=True
    )

    assert "activeSearchSessionId" in javascript

    assert (
        "searchResponse.search_id"
        in javascript
    )

    assert (
        "continueSearchConversation"
        in javascript
    )

    assert (
        "/continue"
        in javascript
    )

    assert (
        "continuationResponse.response"
        in javascript
    )

    assert (
        "Reviewing your current results..."
        in javascript
    )

    assert (
        "latestSearchRequestId += 1"
        in javascript
    )

    assert (
        "input.disabled = false"
        in javascript
    )

    assert (
        "submitButton.disabled = true"
        in javascript
    )

    assert "resetSearchComposer" in javascript

    assert (
        "data-new-chat-button"
        in html
    )


def test_dashboard_persists_selected_location(client):
    response = client.get(
        "/static/js/dashboard.js"
    )

    assert response.status_code == 200

    javascript = response.get_data(
        as_text=True
    )

    assert (
        'LOCATION_STORAGE_KEY =\n'
        '  "cityguide:selected-location"'
        in javascript
    )

    assert "window.localStorage.getItem" in javascript
    assert "window.localStorage.setItem" in javascript
    assert "window.localStorage.removeItem" in javascript
    assert "loadStoredLocation" in javascript
    assert "saveSelectedLocation" in javascript
    assert "isValidStoredLocation" in javascript

    assert (
        "loadStoredLocation() ||"
        in javascript
    )

    assert (
        "saveSelectedLocation(selectedLocation)"
        in javascript
    )


def test_dashboard_uses_compact_place_action_labels(client):
    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert javascript_response.status_code == 200
    assert stylesheet_response.status_code == 200

    javascript = javascript_response.get_data(
        as_text=True
    )

    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert 'label: "Directions"' in javascript
    assert 'label: "Call"' in javascript
    assert 'label: "Website"' in javascript

    assert (
        "ariaLabel: `Get directions to ${place.name}`"
        in javascript
    )

    assert (
        "ariaLabel: `Call ${place.name}`"
        in javascript
    )

    assert (
        "ariaLabel: `Visit ${place.name} website`"
        in javascript
    )

    assert (
        ".recommendation-actions {\n"
        "  display: grid;"
        in stylesheet
    )


def test_dashboard_places_photo_thumbnails_below_hero(client, app):
    authenticate_client(client, app)

    dashboard_response = client.get(
        "/dashboard"
    )

    javascript_response = client.get(
        "/static/js/dashboard.js"
    )

    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert dashboard_response.status_code == 200
    assert javascript_response.status_code == 200
    assert stylesheet_response.status_code == 200

    html = dashboard_response.get_data(
        as_text=True
    )

    javascript = javascript_response.get_data(
        as_text=True
    )

    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    hero_position = html.index(
        'class="place-hero place-hero--one"'
    )

    gallery_position = html.index(
        'class="place-gallery-strip"'
    )

    details_position = html.index(
        'class="place-details-content"'
    )

    assert hero_position < gallery_position
    assert gallery_position < details_position

    assert ".slice(0, 5)" in javascript
    assert "SELECTORS.placeGallery" in javascript

    assert (
        "grid-template-columns: repeat(5, minmax(0, 1fr));"
        in stylesheet
    )

    assert "aspect-ratio: 4 / 3;" in stylesheet

    assert (
        "0 0 0 2px var(--dashboard-accent-soft);"
        in stylesheet
    )

    assert (
        "grid-template-columns: repeat(4, minmax(0, 1fr));"
        in stylesheet
    )


def test_dashboard_uses_discovery_focused_sidebar(client, app):
    authenticate_client(client, app)

    response = client.get("/dashboard")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    expected_labels = [
        "New Search",
        "Explore",
        "Saved Places",
        "Categories",
        "Student Deals",
        "Community Picks",
        "History",
    ]

    for label in expected_labels:
        assert label in html

    assert "New Chat" not in html
    assert "Recent chats" not in html
    assert ">Home<" not in html
    assert ">Recent<" not in html
    assert ">Collections<" not in html
    assert 'data-lucide="compass"' in html
    assert 'data-lucide="layout-grid"' in html
    assert 'data-lucide="badge-percent"' in html
    assert 'data-lucide="users"' in html
    assert 'data-lucide="history"' in html


def test_dashboard_supports_local_saved_places(client, app):
    authenticate_client(client, app)

    dashboard_response = client.get("/dashboard")
    javascript_response = client.get(
        "/static/js/dashboard.js"
    )
    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert dashboard_response.status_code == 200
    assert javascript_response.status_code == 200
    assert stylesheet_response.status_code == 200

    html = dashboard_response.get_data(as_text=True)
    javascript = javascript_response.get_data(
        as_text=True
    )
    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert html.count("data-place-save-button") == 2
    assert 'data-place-save-label' in html
    assert 'aria-pressed="false"' in html

    assert (
        '"cityguide:saved-place-ids"'
        in javascript
    )
    assert "loadSavedPlaceIds" in javascript
    assert "persistSavedPlaceIds" in javascript
    assert "toggleSavedPlace" in javascript
    assert "updateSavedPlaceButtons" in javascript
    assert "initializeSavedPlaces" in javascript
    assert "button.dataset.placeId = place.id" in javascript

    assert (
        ".place-save-control--saved"
        in stylesheet
    )
    assert "fill: currentColor;" in stylesheet


def test_dashboard_contains_saved_places_view(client, app):
    authenticate_client(client, app)

    dashboard_response = client.get("/dashboard")
    javascript_response = client.get(
        "/static/js/dashboard.js"
    )
    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert dashboard_response.status_code == 200
    assert javascript_response.status_code == 200
    assert stylesheet_response.status_code == 200

    html = dashboard_response.get_data(as_text=True)
    javascript = javascript_response.get_data(
        as_text=True
    )
    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert (
        'data-dashboard-navigation="explore"'
        in html
    )
    assert (
        'data-dashboard-navigation="saved"'
        in html
    )
    assert 'data-dashboard-view="saved"' in html
    assert 'data-saved-places-list' in html
    assert 'data-saved-places-empty' in html
    assert "No saved places yet" in html

    assert (
        '"cityguide:saved-places"'
        in javascript
    )
    assert "createSavedPlaceRecord" in javascript
    assert "renderSavedPlacesView" in javascript
    assert "setDashboardView" in javascript
    assert (
        "initializeDashboardNavigation"
        in javascript
    )

    assert (
        ".dashboard-shell--saved-view"
        in stylesheet
    )
    assert ".saved-places-view" in stylesheet
    assert ".saved-places-empty" in stylesheet


def test_dashboard_contains_discovery_hub(client, app):
    authenticate_client(client, app)

    dashboard_response = client.get("/dashboard")
    javascript_response = client.get(
        "/static/js/dashboard.js"
    )
    stylesheet_response = client.get(
        "/static/css/dashboard.css"
    )

    assert dashboard_response.status_code == 200
    assert javascript_response.status_code == 200
    assert stylesheet_response.status_code == 200

    html = dashboard_response.get_data(as_text=True)
    javascript = javascript_response.get_data(
        as_text=True
    )
    stylesheet = stylesheet_response.get_data(
        as_text=True
    )

    assert (
        'data-dashboard-navigation="categories"'
        in html
    )
    assert (
        'data-dashboard-view="categories"'
        in html
    )
    assert "data-discovery-location" in html
    assert "data-discovery-mood-grid" in html
    assert "data-discovery-status" in html
    assert "data-discovery-collections" in html
    assert "discovery-surprise-button" in html
    assert 'id="categories-title"' in html
    assert "Discover" in html
    assert "Surprise me" in html

    assert "DISCOVERY_MOODS" in javascript
    assert "fetchDiscoveryCollections" in javascript
    assert '"/api/v1/discovery"' in javascript
    assert "createDiscoveryMood" in javascript
    assert "createDiscoveryTile" in javascript
    assert "createDiscoveryCollection" in javascript
    assert "renderDiscoveryHub" in javascript
    assert "launchDiscoverySearch" in javascript
    assert "initializeDiscoveryHub" in javascript
    assert "discoveryCacheKey" in javascript
    assert "discoveryMoodPreviews" in javascript
    assert "discovery-mood-photo" in javascript
    assert "buildPlacePhotoUrl" in javascript
    assert "updateDiscoveryLocation" in javascript
    assert "message-avatar-logo" in javascript
    assert (
        '"/static/images/instead-logo.svg"'
        in javascript
    )
    assert "✦" not in javascript

    assert ".discovery-hero" in stylesheet
    assert ".discovery-mood-grid" in stylesheet
    assert ".discovery-mood" in stylesheet
    assert ".discovery-mood-photo" in stylesheet
    assert ".discovery-mood-overlay" in stylesheet
    assert ".discovery-mood-title" in stylesheet
    assert ".discovery-collections" in stylesheet
    assert ".discovery-track" in stylesheet
    assert ".discovery-tile" in stylesheet
    assert ".discovery-tile-photo" in stylesheet
    assert ".discovery-loading-state" in stylesheet
    assert ".discovery-photo-attribution" in stylesheet
    assert ".message-avatar-logo" in stylesheet

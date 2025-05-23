/**
 * @file webroot/sources/app.js
 * @description Main client-side JavaScript for EmbryGo.
 *              Includes HTMX CSRF configuration.
 */

/**
 * Configures HTMX to automatically include the CSRF token in relevant requests.
 * Reads the token from a meta tag named 'csrf-token'.
 */
function configureHtmxCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    let token = null;
    if (meta) {
        token = meta.getAttribute('content');
    }

    if (token && token !== "csrf-disabled" && token !== "csrf-api-excluded") {
        document.body.addEventListener('htmx:configRequest', function(event) {
            const method = event.detail.verb.toUpperCase();
            // Add CSRF token for state-changing HTTP methods
            if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
                event.detail.headers['X-CSRF-Token'] = token;
                // console.debug("CSRF token added to HTMX request:", method, event.detail.path);
            }
        });
        console.info("HTMX CSRF protection configured.");
    } else {
        if (token === "csrf-disabled") {
            console.warn("HTMX CSRF protection explicitly disabled by server config for this page/context.");
        } else if (token === "csrf-api-excluded") {
             console.info("HTMX CSRF protection not applied as this route is likely an API excluded from CSRF.");
        } else {
            console.warn("CSRF token meta tag not found or token is empty. HTMX CSRF protection may not be active.");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("EmbryGo app.js loaded.");
    configureHtmxCsrf();
    // Add any other client-side initializations here
});
import { UserManager } from "https://cdn.jsdelivr.net/npm/oidc-client-ts@3.0.1/+esm";

const cognitoAuthConfig = {
    authority: "https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_uKRxqbEX5",
    client_id: "6kmkgdkls92qfthrbglelcsdjm",
    redirect_uri: window.location.origin + "/",
    response_type: "code",
    scope: "phone openid email"
};

// Create UserManager instance
export const userManager = new UserManager({
    ...cognitoAuthConfig,
});

// Sign out function
export async function signOutRedirect() {
    const clientId = "6kmkgdkls92qfthrbglelcsdjm";
    const logoutUri = "https://dbziso5b0wjgl.cloudfront.net/";
    const cognitoDomain = "https://travel-assistant.auth.eu-central-1.amazoncognito.com";
    
    // Clear local session
    await userManager.removeUser();
    localStorage.clear();
    
    // Redirect to Cognito logout
    window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`;
}

// Get current user
export async function getUser() {
    return await userManager.getUser();
}

// Check if user is authenticated
export async function isAuthenticated() {
    const user = await getUser();
    return user !== null && !user.expired;
}

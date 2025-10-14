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
    try {
        // Clear the user session
        await userManager.removeUser();
        
        // Clear any additional session storage
        sessionStorage.clear();
        localStorage.removeItem('oidc.user:' + cognitoAuthConfig.authority + ':' + cognitoAuthConfig.client_id);
        
        // Redirect to home page
        window.location.href = cognitoAuthConfig.redirect_uri;
    } catch (error) {
        console.error('Error during signout:', error);
        // Force redirect anyway
        window.location.href = cognitoAuthConfig.redirect_uri;
    }
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

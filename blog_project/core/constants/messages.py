HTTP_200_OK                    = 200
HTTP_201_CREATED               = 201
HTTP_204_NO_CONTENT            = 204
HTTP_400_BAD_REQUEST           = 400
HTTP_401_UNAUTHORIZED          = 401
HTTP_403_FORBIDDEN             = 403
HTTP_404_NOT_FOUND             = 404
HTTP_409_CONFLICT              = 409
HTTP_422_UNPROCESSABLE_ENTITY  = 422
HTTP_429_TOO_MANY_REQUESTS     = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500

class AuthMessages:
    REGISTER_SUCCESS        = "Registration successful."
    LOGIN_SUCCESS           = "Login successful."
    LOGOUT_SUCCESS          = "Logged out successfully."
    TOKEN_REFRESH_SUCCESS   = "Token refreshed successfully."
    PASSWORD_CHANGE_SUCCESS = "Password changed. Please log in again."
    PASSWORD_RESET_SUCCESS  = "Password reset successful. You can now log in."
    FORGOT_PASSWORD_SAFE    = "If an account with this email exists, a reset link has been sent."

    INVALID_CREDENTIALS    = "Invalid email or password."
    ACCOUNT_DEACTIVATED    = "This account has been deactivated."
    REFRESH_TOKEN_REQUIRED = "refresh_token is required."
    INVALID_REFRESH_TOKEN  = "Invalid or expired refresh token."
    REGISTER_FAILED        = "Registration failed."
    LOGIN_FAILED           = "Login failed."
    PASSWORD_CHANGE_FAILED = "Password change failed."
    PASSWORD_RESET_FAILED  = "Password reset failed."
    INVALID_REQUEST        = "Invalid request."
    CANNOT_CHANGE_OWN_ROLE = "You cannot change your own role."
    ROLE_CHANGE_FAILED     = "Role change failed."

class UserMessages:
    PROFILE_FETCHED  = "Profile fetched successfully."
    PROFILE_UPDATED  = "Profile updated successfully."
    ACCOUNT_DELETED  = "Account deleted successfully."
    LIST_FETCHED     = "Users fetched successfully."
    DETAIL_FETCHED   = "User details fetched successfully."
    UPDATE_FAILED    = "Update failed."
    NOT_FOUND        = "User not found."
    FORBIDDEN        = "You can only update your own account."
    DELETE_FORBIDDEN = "You can only delete your own account."


class SubscriptionMessages:
    SUBSCRIBED          = "Subscribed to {author}."
    UNSUBSCRIBED        = "Unsubscribed from {author}."
    ALREADY_SUBSCRIBED  = "You are already subscribed."
    NOT_SUBSCRIBED      = "You are not subscribed to this author."
    SELF_SUBSCRIBE      = "You cannot subscribe to yourself."
    MY_SUBS_FETCHED     = "Subscriptions fetched successfully."
    SUBSCRIBERS_FETCHED = "Subscribers fetched successfully."

class BlogMessages:
    CREATED         = "Blog created successfully."
    UPDATED         = "Blog updated successfully."
    DELETED         = "Blog deleted successfully."
    FETCHED         = "Blog fetched successfully."
    LIST_FETCHED    = "Blogs fetched successfully."
    PUBLISHED       = "Blog published successfully."
    UNPUBLISHED     = "Blog unpublished successfully."
    NOT_FOUND       = "Blog not found."
    NOT_PUBLISHED   = "This blog is not published yet."
    CREATE_FAILED   = "Blog creation failed."
    UPDATE_FAILED   = "Blog update failed."
    EDIT_FORBIDDEN  = "You can only edit your own blogs."
    DEL_FORBIDDEN   = "You can only delete your own blogs."
    PUB_FORBIDDEN   = "You can only publish your own blogs."
    NO_AUTHOR       = ("This blog has no author assigned and cannot be published. "
                       "Please assign an author via the admin panel first.")
    IS_PUB_REQUIRED = "is_published field is required."
    AUTH_REQUIRED   = "Authentication required."


class TopicMessages:
    CREATED        = "Topic created successfully."
    DELETED        = "Topic deleted successfully."
    FETCHED        = "Topic fetched successfully."
    LIST_FETCHED   = "Topics fetched successfully."
    NOT_FOUND      = "Topic not found."
    CREATE_FAILED  = "Topic creation failed."
    DELETE_BLOCKED = "Cannot delete — blogs exist under this topic."

class CommentMessages:
    CREATED        = "Comment added successfully."
    UPDATED        = "Comment updated successfully."
    DELETED        = "Comment deleted successfully."
    LIST_FETCHED   = "Comments fetched successfully."
    CREATE_FAILED  = "Comment creation failed."
    UPDATE_FAILED  = "Comment update failed."
    EDIT_FORBIDDEN = "You can only edit your own comments."
    DEL_FORBIDDEN  = "You cannot delete this comment."

class PermissionMessages:
    ADMIN_ONLY      = "Only admins can perform this action."
    AUTHOR_ONLY     = "Only authors can perform this action."
    AUTHOR_OR_ADMIN = "Only authors can create or modify content."
    OWNER_OR_ADMIN  = "You can only modify your own content."
    AUTH_REQUIRED   = "Authentication credentials were not provided."
    FORBIDDEN       = "You do not have permission to perform this action."

class GenericMessages:
    SERVER_ERROR   = "An unexpected error occurred. Please try again later."
    NOT_FOUND      = "The requested resource was not found."
    THROTTLED      = "Too many requests. Please slow down."
    VALIDATION_ERR = "Validation error."
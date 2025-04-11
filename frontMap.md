# Real Estate Auction Platform - Frontend Project Structure

```
src/
├── app.html
├── app.postcss  # Tailwind setup
├── hooks.server.js  # Handle auth on server routes
├── lib/
│   ├── assets/
│   │   └── images/
│   ├── components/
│   │   ├── auction/
│   │   │   ├── AuctionCard.svelte
│   │   │   ├── AuctionDetails.svelte
│   │   │   ├── AuctionForm.svelte
│   │   │   ├── BidForm.svelte
│   │   │   └── BidHistory.svelte
│   │   ├── auth/
│   │   │   ├── LoginForm.svelte
│   │   │   ├── RegisterForm.svelte
│   │   │   ├── ResetPasswordForm.svelte
│   │   │   └── VerifyEmailForm.svelte
│   │   ├── common/
│   │   │   ├── Alert.svelte
│   │   │   ├── Avatar.svelte
│   │   │   ├── Footer.svelte
│   │   │   ├── Header.svelte
│   │   │   ├── Modal.svelte
│   │   │   ├── Pagination.svelte
│   │   │   └── Sidebar.svelte
│   │   ├── contract/
│   │   │   ├── ContractCard.svelte
│   │   │   ├── ContractDetails.svelte
│   │   │   └── ContractForm.svelte
│   │   ├── dashboard/
│   │   │   ├── AdminDashboard.svelte
│   │   │   ├── BuyerDashboard.svelte
│   │   │   ├── DashboardCard.svelte
│   │   │   ├── DashboardStats.svelte
│   │   │   └── SellerDashboard.svelte
│   │   ├── message/
│   │   │   ├── MessageList.svelte
│   │   │   └── MessageThread.svelte
│   │   ├── property/
│   │   │   ├── PropertyCard.svelte
│   │   │   ├── PropertyDetails.svelte
│   │   │   ├── PropertyForm.svelte
│   │   │   └── PropertyImages.svelte
│   │   └── user/
│   │       ├── ProfileForm.svelte
│   │       └── UserRoles.svelte
│   ├── config/
│   │   ├── api.js
│   │   └── constants.js
│   ├── services/
│   │   ├── auctionService.js
│   │   ├── authService.js
│   │   ├── contractService.js
│   │   ├── documentService.js
│   │   ├── messageService.js
│   │   ├── notificationService.js
│   │   ├── propertyService.js
│   │   └── userService.js
│   ├── stores/
│   │   ├── auctions.js
│   │   ├── auth.js
│   │   ├── contracts.js
│   │   ├── messages.js
│   │   ├── notifications.js
│   │   ├── properties.js
│   │   └── ui.js
│   └── utils/
│       ├── api.js
│       ├── dateUtils.js
│       ├── fileUtils.js
│       ├── formatters.js
│       ├── permissions.js
│       ├── tokenManager.js
│       └── validators.js
└── routes/
    ├── +layout.server.js
    ├── +layout.svelte
    ├── +page.svelte
    ├── auctions/
    │   ├── +page.server.js
    │   ├── +page.svelte
    │   ├── [id]/
    │   │   ├── +page.server.js
    │   │   ├── +page.svelte
    │   │   ├── bids/
    │   │   │   └── +page.svelte
    │   │   └── documents/
    │   │       └── +page.svelte
    │   └── create/
    │       └── +page.svelte
    ├── auth/
    │   ├── login/
    │   │   └── +page.svelte
    │   ├── register/
    │   │   └── +page.svelte
    │   ├── reset-password/
    │   │   └── +page.svelte
    │   └── verify-email/
    │       └── +page.svelte
    ├── contracts/
    │   ├── +page.svelte
    │   └── [id]/
    │       └── +page.svelte
    ├── dashboard/
    │   ├── +layout.svelte
    │   └── +page.svelte
    ├── messages/
    │   ├── +page.svelte
    │   └── [id]/
    │       └── +page.svelte
    ├── profile/
    │   ├── +page.svelte
    │   └── [id]/
    │       └── +page.svelte
    └── properties/
        ├── +page.server.js
        ├── +page.svelte
        ├── [id]/
        │   ├── +page.server.js
        │   └── +page.svelte
        └── create/
            └── +page.svelte
```







api.js:226
 POST http://localhost:8000/api/properties/ 400 (Bad Request)
apiRequest	@	api.js:226
post	@	api.js:275
createProperty	@	propertyService.js:111
createProperty	@	properties.js:184
handleSubmit	@	+page.svelte:193
(anonymous)	@	PropertyForm.svelte:368
setTimeout
submitResult	@	PropertyForm.svelte:366
handleSubmit	@	PropertyForm.svelte:364
properties.js:203 Error creating property: ApiError: An error occurred
    at handleResponse (api.js:157:9)
    at async apiRequest (api.js:227:10)
    at async Module.createProperty (propertyService.js:111:20)
    at async Object.createProperty (properties.js:184:25)
createProperty	@	properties.js:203
await in createProperty
handleSubmit	@	+page.svelte:193
(anonymous)	@	PropertyForm.svelte:368
setTimeout
submitResult	@	PropertyForm.svelte:366
handleSubmit	@	PropertyForm.svelte:364
+page.svelte:211 Property Creation Error: ApiError: An error occurred
    at handleResponse (api.js:157:9)
    at async apiRequest (api.js:227:10)
    at async Module.createProperty (propertyService.js:111:20)
    at async Object.createProperty (properties.js:184:25)

﻿

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







"""
Error checking slug uniqueness: 'function' object has no attribute 'connection'
[12/Apr/2025 07:43:14] "POST /api/properties/ HTTP/1.1" 201 1284
[12/Apr/2025 07:43:14] "OPTIONS /api/properties/1/images/ HTTP/1.1" 200 0
Bad Request: /api/properties/1/images/
[12/Apr/2025 07:43:14] "POST /api/properties/1/images/ HTTP/1.1" 400 104
Bad Request: /api/properties/1/images/
[12/Apr/2025 07:43:14] "POST /api/properties/1/images/ HTTP/1.1" 400 104
"""

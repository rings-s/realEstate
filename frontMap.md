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
+page.svelte:76 Submit error: ReferenceError: key is not defined
    at createProperty (properties.js:147:15)
    at Object.handleSubmit (+page.svelte:69:28)
    at HTMLFormElement.handleSubmit (PropertyForm.svelte:549:3)
properties.js:164 Property creation error details: ReferenceError: key is not defined
    at createProperty (properties.js:147:15)
    at Object.handleSubmit (+page.svelte:69:28)
    at HTMLFormElement.handleSubmit (PropertyForm.svelte:549:3)
+page.svelte:76 Submit error: ReferenceError: key is not defined
    at createProperty (properties.js:147:15)
    at Object.handleSubmit (+page.svelte:69:28)
    at HTMLFormElement.handleSubmit (PropertyForm.svelte:549:3)
properties.js:164 Property creation error details: ReferenceError: key is not defined
    at createProperty (properties.js:147:15)
    at Object.handleSubmit (+page.svelte:69:28)
    at HTMLFormElement.handleSubmit (PropertyForm.svelte:549:3)
+page.svelte:76 Submit error: ReferenceError: key is not defined
    at createProperty (properties.js:147:15)
    at Object.handleSubmit (+page.svelte:69:28)
    at HTMLFormElement.handleSubmit (PropertyForm.svelte:549:3)

﻿

/src/app.css
10:03:05 AM [vite] (ssr) page reload src/routes/properties/add/+page.svelte
[vite:css][postcss] @import must precede all other statements (besides @charset or empty @layer)
2350|    }
2351|  }
2352|  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
   |  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2353|  :root {
2354|    --sidebar-width: 280px;
10:03:13 AM [vite] (client) hmr update /src/routes/properties/add/+page.svelte, /src/app.css
10:03:13 AM [vite] (ssr) page reload src/routes/properties/add/+page.svelte
[vite:css][postcss] @import must precede all other statements (besides @charset or empty @layer)
2350|    }
2351|  }
2352|  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
   |  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2353|  :root {
2354|    --sidebar-width: 280px;
[vite:css][postcss] @import must precede all other statements (besides @charset or empty @layer)
2350|    }
2351|  }
2352|  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
   |  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2353|  :root {
2354|    --sidebar-width: 280px; (x2)
[vite:css][postcss] @import must precede all other statements (besides @charset or empty @layer)
2350|    }
2351|  }
2352|  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
   |  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2353|  :root {
2354|    --sidebar-width: 280px; (x3)








"""

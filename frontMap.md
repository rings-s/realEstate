frontend/
├── src/
│   ├── lib/
│   │   ├── components/          # المكونات القابلة لإعادة الاستخدام
│   │   ├── services/            # خدمات التكامل مع API
│   │   ├── stores/              # إدارة الحالة (State Management)
│   │   ├── utils/               # الدوال المساعدة
│   │   └── styles/              # الأنماط العامة
│   ├── routes/                  # مسارات التطبيق
│   ├── app.html                 # قالب HTML الرئيسي
│   └── hooks.server.js          # معالجة الاستيقان على الخادم
├── static/                      # الملفات الثابتة
│   ├── fonts/                   # الخطوط العربية
│   └── images/                  # الصور
├── svelte.config.js             # إعدادات SvelteKit
└── package.json                 # التبعيات البرمجية





src/lib/components/
├── common/                      # عناصر واجهة المستخدم المشتركة
│   ├── Button.svelte            # زر قابل للتخصيص
│   ├── Input.svelte             # حقل إدخال
│   ├── Select.svelte            # قائمة منسدلة
│   ├── Checkbox.svelte          # مربع اختيار
│   ├── Modal.svelte             # نافذة منبثقة
│   ├── Alert.svelte             # تنبيهات
│   ├── Loader.svelte            # مؤشر التحميل
│   ├── Pagination.svelte        # ترقيم الصفحات
│   ├── Breadcrumb.svelte        # شريط التنقل التسلسلي
│   └── Card.svelte              # بطاقة عرض
├── layout/                      # مكونات التخطيط
│   ├── Header.svelte            # الرأس
│   ├── Footer.svelte            # التذييل
│   ├── Sidebar.svelte           # الشريط الجانبي
│   ├── Navbar.svelte            # شريط التنقل
│   └── MainLayout.svelte        # التخطيط الرئيسي
├── auth/                        # مكونات المصادقة
│   ├── LoginForm.svelte         # نموذج تسجيل الدخول
│   ├── RegisterForm.svelte      # نموذج التسجيل
│   ├── ResetPasswordForm.svelte # نموذج استعادة كلمة المرور
│   └── VerifyEmailForm.svelte   # نموذج تأكيد البريد الإلكتروني
├── properties/                  # مكونات العقارات
│   ├── PropertyCard.svelte      # بطاقة عرض العقار
│   ├── PropertyDetails.svelte   # تفاصيل العقار
│   ├── PropertyForm.svelte      # نموذج إضافة/تعديل العقار
│   ├── PropertyFilters.svelte   # فلترة العقارات
│   └── PropertyMap.svelte       # خريطة العقار
├── auctions/                    # مكونات المزادات
│   ├── AuctionCard.svelte       # بطاقة عرض المزاد
│   ├── AuctionDetails.svelte    # تفاصيل المزاد
│   ├── BidForm.svelte           # نموذج تقديم العروض
│   ├── BidHistory.svelte        # سجل العروض
│   ├── AuctionTimer.svelte      # عداد المزاد التنازلي
│   └── AuctionForm.svelte       # نموذج إضافة/تعديل المزاد
├── contracts/                   # مكونات العقود
│   ├── ContractCard.svelte      # بطاقة عرض العقد
│   ├── ContractDetails.svelte   # تفاصيل العقد
│   ├── ContractForm.svelte      # نموذج إنشاء العقد
│   └── SignatureArea.svelte     # منطقة التوقيع
├── dashboard/                   # مكونات لوحة التحكم
│   ├── DashboardStats.svelte    # إحصائيات لوحة التحكم
│   ├── ActivityFeed.svelte      # سجل النشاطات
│   ├── SellerDashboard.svelte   # لوحة تحكم البائع
│   ├── BuyerDashboard.svelte    # لوحة تحكم المشتري
│   ├── AgentDashboard.svelte    # لوحة تحكم الوكيل
│   ├── InspectorDashboard.svelte # لوحة تحكم المفتش
│   └── AdminDashboard.svelte    # لوحة تحكم المدير
└── notifications/               # مكونات الإشعارات
    ├── NotificationBell.svelte  # جرس الإشعارات
    ├── NotificationItem.svelte  # عنصر إشعار
    └── NotificationCenter.svelte # مركز الإشعارات




src/lib/services/
├── api.js                      # الإعدادات الأساسية للاتصال بالـ API
├── auth.js                     # خدمات المصادقة وإدارة المستخدمين
├── properties.js               # خدمات العقارات
├── auctions.js                 # خدمات المزادات
├── bids.js                     # خدمات العروض
├── contracts.js                # خدمات العقود
├── documents.js                # خدمات المستندات
├── payments.js                 # خدمات المدفوعات
├── messages.js                 # خدمات الرسائل
└── notifications.js            # خدمات الإشعارات



src/lib/stores/
├── auth.js                     # حالة الاستيقان والمستخدم
├── properties.js               # حالة العقارات
├── auctions.js                 # حالة المزادات النشطة
├── notifications.js            # حالة الإشعارات
├── ui.js                       # حالة واجهة المستخدم (التحميل، الأخطاء)
└── rtc.js                      # حالة الاتصال في الوقت الفعلي



src/lib/utils/
├── validation.js               # التحقق من صحة النماذج
├── formatting.js               # تنسيق البيانات (تواريخ، عملات)
├── permissions.js              # التحقق من صلاحيات المستخدم
├── arabic.js                   # مساعدات خاصة باللغة العربية
└── websocket.js                # إدارة اتصالات WebSocket


src/routes/
├── +layout.svelte               # Main application layout
├── +page.svelte                 # Home page
├── login/                       # Login routes
│   └── +page.svelte
├── register/                    # Registration routes
│   └── +page.svelte
├── password-reset/              # Password reset routes
│   └── +page.svelte
├── email-verification/          # Email verification routes
│   └── +page.svelte
├── properties/                  # Property routes
│   ├── +page.svelte             # Properties list
│   ├── add/                     # Add new property
│   │   └── +page.svelte
│   └── [slug]/                  # Property details (using slug)
│       └── +page.svelte
├── auctions/                    # Auction routes
│   ├── +page.svelte             # Auctions list
│   ├── add/                     # Create new auction
│   │   └── +page.svelte
│   └── [slug]/                  # Auction details (using slug)
│       └── +page.svelte
├── contracts/                   # Contract routes
│   ├── +page.svelte             # Contracts list
│   ├── add/                     # Create new contract
│   │   └── +page.svelte
│   └── [contract_number]/       # Contract details (using contract number)
│       └── +page.svelte
├── documents/                   # Document routes
│   ├── +page.svelte             # Documents list
│   ├── upload/                  # Upload new document
│   │   └── +page.svelte
│   └── [document_number]/       # Document details (using document number)
│       └── +page.svelte
├── payments/                    # Payment routes
│   ├── +page.svelte             # Payments list
│   ├── add/                     # Create new payment
│   │   └── +page.svelte
│   └── [payment_number]/        # Payment details (using payment number)
│       └── +page.svelte
├── messages/                    # Message routes
│   ├── +page.svelte             # Message threads list
│   └── [slug]/                  # Thread details (using slug)
│       └── +page.svelte
├── profile/                     # Profile routes
│   ├── +page.svelte             # View profile
│   └── edit/                    # Edit profile
│       └── +page.svelte
└── dashboard/                   # Dashboard routes
    ├── +page.svelte             # Main dashboard
    ├── seller/                  # Seller dashboard
    │   └── +page.svelte
    ├── buyer/                   # Buyer dashboard
    │   └── +page.svelte
    ├── agent/                   # Agent dashboard
    │   └── +page.svelte
    ├── inspector/               # Inspector dashboard
    │   └── +page.svelte
    └── admin/                   # Admin dashboard
        └── +page.svelte

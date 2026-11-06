from app.schemas.common import MessageResponse, PaginationMeta, PaginatedResponse
from app.schemas.auth import (
    LoginRequest, TokenUserData, TokenResponse, RefreshTokenRequest,
    PasswordChangeRequest, LogoutRequest
)
from app.schemas.user import (
    UserCreate, UserUpdate, UserStatusUpdate, UserRoleAssign,
    UserResponse, UserActivityLogResponse
)
from app.schemas.registration import (
    CustomerRegisterRequest, VerifyEmailRequest, ResendVerificationRequest,
    RegistrationResponse
)
from app.schemas.profile import (
    CustomerProfileUpdate, CustomerProfileResponse, DeactivationRequestCreate,
    DeactivationReviewRequest, ProfileChangeHistoryResponse
)
from app.schemas.address import (
    AddressCreate, AddressUpdate, AddressResponse,
    OrderAddressAssociationRequest, MockOrderResponse
)
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode, CategoryBreadcrumb
)
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductDetailResponse
from app.schemas.variant import VariantCreate, VariantUpdate, VariantStockAdjust, VariantResponse
from app.schemas.media import ProductMediaResponse, MediaMetadataUpdate

# Modules 11 - 14
from app.schemas.attribute import (
    AttributeCreate, AttributeUpdate, AttributeResponse, AttributeOptionCreate,
    AttributeOptionResponse, CategoryAttributeAssign, CategoryAttributeResponse,
    ProductAttributeAssign, ProductAttributeValueResponse
)
from app.schemas.pricing import (
    PriceCreate, PriceUpdate, PriceResponse, PriceHistoryResponse
)
from app.schemas.inventory import (
    StockAdditionRequest, StockReductionRequest, StockReservationRequest,
    StockReleaseRequest, InventoryItemResponse, StockMovementResponse
)
from app.schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    WarehouseStockAssignRequest, WarehouseInventoryResponse
)

# Modules 15 - 25
from app.schemas.transfer import TransferCreate, TransferDispatch, TransferReceive, TransferResponse
from app.schemas.low_stock import (
    ThresholdConfigure, ThresholdResponse, ThresholdHistoryResponse,
    RestockAlertResponse, LowStockReportItem
)
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartItemResponse, CartResponse
from app.schemas.wishlist import WishlistItemAdd, WishlistItemResponse
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse, CouponValidateRequest, CouponValidateResponse
from app.schemas.promotion import PromotionCreate, PromotionResponse, PromotionHistoryResponse
from app.schemas.tax import (
    TaxRateCreate, TaxRateUpdate, TaxRateResponse, TaxHistoryResponse,
    TaxCalculationRequest, TaxCalculationResponse
)
from app.schemas.shipping import (
    ShippingMethodCreate, ShippingMethodResponse, ShippingEstimateRequest,
    ShippingEstimateOption, ShippingEstimateResponse
)
from app.schemas.checkout import (
    CalculationItemDetail, CartCalculationRequest, CartCalculationSummary,
    CheckoutInitRequest, CheckoutSessionResponse
)
from app.schemas.order import OrderItemResponse, OrderStatusHistoryResponse, OrderResponse, OrderStatusUpdate

# Modules 41 - 49
from app.schemas.notification import NotificationCreate, NotificationResponse, UnreadCountResponse
from app.schemas.messaging import ProviderConfigCreate, ProviderConfigResponse, SendMessageRequest, MessageLogResponse
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierApprovalUpdate, SupplierResponse,
    SupplierHistoryResponse, ProductSupplierCreate, ProductSupplierResponse
)
from app.schemas.purchase_order import (
    POCreateItem, POCreate, POResponseItem, POResponse,
    POStatusHistoryResponse, POStatusUpdate, POReceiveItem, POReceiveRequest
)
from app.schemas.supplier_invoice import SupplierInvoiceCreate, SupplierInvoicePaymentUpdate, SupplierInvoiceResponse
from app.schemas.audit_entry import AuditLogEntryCreate, AuditLogEntryResponse
from app.schemas.dashboard import DashboardSummaryResponse, CustomerDashboardResponse
from app.schemas.analytics import (
    DailySalesMetric, SalesAnalyticsResponse, WarehouseStockMetric, InventoryAnalyticsResponse,
    PaymentStatusMetric, PaymentAnalyticsResponse, TopProductPerformance, CategoryPerformance,
    PerformanceAnalyticsResponse
)
from app.schemas.background_task import TaskExportRequest, ScheduleSummaryRequest, TaskResponse

# Modules 26 - 40
from app.schemas.order_item import OrderItemFulfillmentUpdate, OrderItemDetailResponse
from app.schemas.order_status import OrderStatusTransitionRequest, PermittedTransitionsResponse
from app.schemas.order_cancellation import OrderCancellationCreate, OrderCancellationResponse
from app.schemas.payment import (
    PaymentInitiate, PaymentProcessSandbox, PaymentWebhook,
    PaymentTransactionResponse, PaymentResponse
)
from app.schemas.refund import RefundCreate, RefundResponse
from app.schemas.cod import (
    CODConfigUpdate, CODConfigResponse, CODEligibilityCheck,
    CODEligibilityResponse, CODRecordCollection, CODCollectionResponse
)
from app.schemas.shipment import (
    ShipmentCreate, ShipmentDispatch, TrackingEventCreate, TrackingEventResponse,
    DeliveryAssignmentResponse, ShipmentResponse, DeliveryAssignRequest,
    DeliveryAttemptRequest, DeliveryConfirmRequest
)
from app.schemas.return_exchange import (
    ReturnItemCreate, ReturnItemResponse, ReturnRequestCreate, ReturnReview,
    ReturnRequestResponse, ExchangeRequestCreate, ExchangeReview, ExchangeRequestResponse
)
from app.schemas.product_review import (
    ProductReviewCreate, ProductReviewModeration, ProductReviewResponse, ProductRatingSummary
)
from app.schemas.product_qa import (
    ProductQuestionCreate, ProductQuestionModeration, ProductAnswerCreate,
    ProductAnswerResponse, ProductQuestionResponse
)
from app.schemas.support_ticket import (
    TicketMessageCreate, TicketMessageResponse, SupportTicketCreate,
    TicketAssignRequest, TicketStatusUpdate, SupportTicketResponse
)

__all__ = [
    "MessageResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "LoginRequest",
    "TokenUserData",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "LogoutRequest",
    "UserCreate",
    "UserUpdate",
    "UserStatusUpdate",
    "UserRoleAssign",
    "UserResponse",
    "UserActivityLogResponse",
    "CustomerRegisterRequest",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "RegistrationResponse",
    "CustomerProfileUpdate",
    "CustomerProfileResponse",
    "DeactivationRequestCreate",
    "DeactivationReviewRequest",
    "ProfileChangeHistoryResponse",
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    "OrderAddressAssociationRequest",
    "MockOrderResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryTreeNode",
    "CategoryBreadcrumb",
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductDetailResponse",
    "VariantCreate",
    "VariantUpdate",
    "VariantStockAdjust",
    "VariantResponse",
    "ProductMediaResponse",
    "MediaMetadataUpdate",
    "AttributeCreate",
    "AttributeUpdate",
    "AttributeResponse",
    "AttributeOptionCreate",
    "AttributeOptionResponse",
    "CategoryAttributeAssign",
    "CategoryAttributeResponse",
    "ProductAttributeAssign",
    "ProductAttributeValueResponse",
    "PriceCreate",
    "PriceUpdate",
    "PriceResponse",
    "PriceHistoryResponse",
    "StockAdditionRequest",
    "StockReductionRequest",
    "StockReservationRequest",
    "StockReleaseRequest",
    "InventoryItemResponse",
    "StockMovementResponse",
    "WarehouseCreate",
    "WarehouseUpdate",
    "WarehouseResponse",
    "WarehouseStockAssignRequest",
    "WarehouseInventoryResponse",
    # 15 - 25
    "TransferCreate",
    "TransferDispatch",
    "TransferReceive",
    "TransferResponse",
    "ThresholdConfigure",
    "ThresholdResponse",
    "ThresholdHistoryResponse",
    "RestockAlertResponse",
    "LowStockReportItem",
    "CartItemAdd",
    "CartItemUpdate",
    "CartItemResponse",
    "CartResponse",
    "WishlistItemAdd",
    "WishlistItemResponse",
    "CouponCreate",
    "CouponUpdate",
    "CouponResponse",
    "CouponValidateRequest",
    "CouponValidateResponse",
    "PromotionCreate",
    "PromotionResponse",
    "PromotionHistoryResponse",
    "TaxRateCreate",
    "TaxRateUpdate",
    "TaxRateResponse",
    "TaxHistoryResponse",
    "TaxCalculationRequest",
    "TaxCalculationResponse",
    "ShippingMethodCreate",
    "ShippingMethodResponse",
    "ShippingEstimateRequest",
    "ShippingEstimateOption",
    "ShippingEstimateResponse",
    "CalculationItemDetail",
    "CartCalculationRequest",
    "CartCalculationSummary",
    "CheckoutInitRequest",
    "CheckoutSessionResponse",
    "OrderItemResponse",
    "OrderStatusHistoryResponse",
    "OrderResponse",
    "OrderStatusUpdate",
    # 41 - 49
    "NotificationCreate",
    "NotificationResponse",
    "UnreadCountResponse",
    "ProviderConfigCreate",
    "ProviderConfigResponse",
    "SendMessageRequest",
    "MessageLogResponse",
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierApprovalUpdate",
    "SupplierResponse",
    "SupplierHistoryResponse",
    "ProductSupplierCreate",
    "ProductSupplierResponse",
    "POCreateItem",
    "POCreate",
    "POResponseItem",
    "POResponse",
    "POStatusHistoryResponse",
    "POStatusUpdate",
    "POReceiveItem",
    "POReceiveRequest",
    "SupplierInvoiceCreate",
    "SupplierInvoicePaymentUpdate",
    "SupplierInvoiceResponse",
    "AuditLogEntryCreate",
    "AuditLogEntryResponse",
    "DashboardSummaryResponse",
    "CustomerDashboardResponse",
    "DailySalesMetric",
    "SalesAnalyticsResponse",
    "WarehouseStockMetric",
    "InventoryAnalyticsResponse",
    "PaymentStatusMetric",
    "PaymentAnalyticsResponse",
    "TopProductPerformance",
    "CategoryPerformance",
    "PerformanceAnalyticsResponse",
    "TaskExportRequest",
    "ScheduleSummaryRequest",
    "TaskResponse",
    "OrderItemFulfillmentUpdate",
    "OrderItemDetailResponse",
    "OrderStatusTransitionRequest",
    "PermittedTransitionsResponse",
    "OrderCancellationCreate",
    "OrderCancellationResponse",
    "PaymentInitiate",
    "PaymentProcessSandbox",
    "PaymentWebhook",
    "PaymentTransactionResponse",
    "PaymentResponse",
    "RefundCreate",
    "RefundResponse",
    "CODConfigUpdate",
    "CODConfigResponse",
    "CODEligibilityCheck",
    "CODEligibilityResponse",
    "CODRecordCollection",
    "CODCollectionResponse",
    "ShipmentCreate",
    "ShipmentDispatch",
    "TrackingEventCreate",
    "TrackingEventResponse",
    "DeliveryAssignmentResponse",
    "ShipmentResponse",
    "DeliveryAssignRequest",
    "DeliveryAttemptRequest",
    "DeliveryConfirmRequest",
    "ReturnItemCreate",
    "ReturnItemResponse",
    "ReturnRequestCreate",
    "ReturnReview",
    "ReturnRequestResponse",
    "ExchangeRequestCreate",
    "ExchangeReview",
    "ExchangeRequestResponse",
    "ProductReviewCreate",
    "ProductReviewModeration",
    "ProductReviewResponse",
    "ProductRatingSummary",
    "ProductQuestionCreate",
    "ProductQuestionModeration",
    "ProductAnswerCreate",
    "ProductAnswerResponse",
    "ProductQuestionResponse",
    "TicketMessageCreate",
    "TicketMessageResponse",
    "SupportTicketCreate",
    "TicketAssignRequest",
    "TicketStatusUpdate",
    "SupportTicketResponse",
]

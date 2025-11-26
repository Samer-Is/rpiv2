# Data Dictionary - Dynamic Pricing Engine MVP

**Generated:** 2025-11-25 12:30:38

**Purpose:** This document provides a comprehensive overview of the database schema for the Dynamic Pricing Engine MVP, focusing on tables critical for demand prediction and pricing optimization.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Tables Summary](#key-tables-summary)
3. [Critical Tables for Dynamic Pricing](#critical-tables-for-dynamic-pricing)
4. [Supporting Tables](#supporting-tables)
5. [Data Constraints and Assumptions](#data-constraints-and-assumptions)
6. [Next Steps](#next-steps)

---

## 1. Overview

The database contains **636 tables** across **12 schemas**, with a total of **6793 columns**.

### Schema Distribution

| Schema | Table Count |
|--------|-------------|
| Migration | 200 |
| Rental | 136 |
| dbo | 126 |
| Fleet | 90 |
| Crm | 58 |
| ConfigurationManagement | 8 |
| Collections | 7 |
| Finance | 5 |
| Archive | 2 |
| Cache | 2 |

## 2. Key Tables Summary

Based on the business requirements for dynamic pricing, we have identified the following key tables categorized by their role:

### UTILIZATION

**Purpose:** Calculate fleet utilization rates (MANDATORY source: Fleet.VehicleHistory)

- **Fleet.VehicleHistory**: 21 columns

### DEMAND

**Purpose:** Analyze booking patterns and rental demand signals

- **Rental.Bookings**: 93 columns
- **Rental.Contract**: 229 columns

### PRICING

**Purpose:** Historical pricing data and rate configurations

- **Rental.RentalRates**: 23 columns

### CONTEXT

**Purpose:** Supporting dimensional data (locations, vehicles, etc.)

- **Fleet.Cities**: 6 columns
- **Fleet.Countries**: 8 columns
- **Fleet.Locations**: 31 columns
- **Fleet.Vehicles**: 68 columns
- **Rental.Branches**: 19 columns
- **Rental.Cities**: 6 columns
- **Rental.Countries**: 8 columns

## 3. Critical Tables for Dynamic Pricing

### Fleet.VehicleHistory

**Purpose:** MANDATORY for utilization calculation

| Column | Data Type | Nullable | PK | Identity | Description |
|--------|-----------|----------|----|---------|--------------|
| Id | int | No | ✓ | ✓ | Identifier/Foreign key |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreatorUserId | bigint | No |  |  | Identifier/Foreign key |
| CreatorUserId | bigint | No |  |  | Identifier/Foreign key |
| OperationId | int | No |  |  | Identifier/Foreign key |
| OperationId | int | No |  |  | Identifier/Foreign key |
| ReferenceNo | nvarchar | No |  |  |  |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| Odometer | int | Yes |  |  |  |
| BranchId | int | Yes |  |  | Identifier/Foreign key |
| CurrentLocationId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | No |  |  | Identifier/Foreign key |
| VehicleId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| AdditionalStatuses | nvarchar | Yes |  |  | Status indicator |
| IsActive | bit | No |  |  |  |
| RowVersion | timestamp | Yes |  |  |  |
| OperationDateTime | datetimeoffset | No |  |  | Timestamp field |
| OldEjarID | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| Comment | nvarchar | Yes |  |  |  |
| Source | int | Yes |  |  |  |

**⚠️ CRITICAL NOTES:**

- This table is the **ONLY** source for utilization calculations (per instructions)
- Must track vehicle status changes over time
- Key columns for analysis: StatusId, VehicleId, CreationTime, OperationDateTime
- Filter all data from 2023-01-01 onwards

### Rental.Contract

**Purpose:** Historical rental contracts and pricing

| Column | Data Type | Nullable | PK | Identity | Description |
|--------|-----------|----------|----|---------|--------------|
| Id | int | No | ✓ |  | Identifier/Foreign key |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| IsDeleted | bit | No |  |  |  |
| DeleterUserId | bigint | Yes |  |  | Identifier/Foreign key |
| DeletionTime | datetime2 | Yes |  |  | Timestamp field |
| ContractNumber | nvarchar | Yes |  |  |  |
| ContractNumber | nvarchar | Yes |  |  |  |
| ContractNumber | nvarchar | Yes |  |  |  |
| ContractNumber | nvarchar | Yes |  |  |  |
| ContractNumber | nvarchar | Yes |  |  |  |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| Start | datetimeoffset | Yes |  |  |  |
| Start | datetimeoffset | Yes |  |  |  |
| Start | datetimeoffset | Yes |  |  |  |
| Start | datetimeoffset | Yes |  |  |  |
| Start | datetimeoffset | Yes |  |  |  |
| Start | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| End | datetimeoffset | Yes |  |  |  |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| PickupOdometer | int | Yes |  |  |  |
| FuelInId | int | Yes |  |  | Identifier/Foreign key |
| RentalRateId | int | Yes |  |  | Identifier/Foreign key |
| DailyRateAmount | decimal | Yes |  |  | Monetary value |
| CurrencyId | int | Yes |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| CustomerId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| FinancialStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| IdentityId | int | No |  |  | Identifier/Foreign key |
| DropoffOdometer | int | Yes |  |  |  |
| FuelOutId | int | Yes |  |  | Identifier/Foreign key |
| FuelCostEnabled | bit | No |  |  |  |
| TransferCostId | int | Yes |  |  | Identifier/Foreign key |
| BookingId | int | Yes |  |  | Identifier/Foreign key |
| BookingId | int | Yes |  |  | Identifier/Foreign key |
| BookingId | int | Yes |  |  | Identifier/Foreign key |
| BookingId | int | Yes |  |  | Identifier/Foreign key |
| BookingId | int | Yes |  |  | Identifier/Foreign key |
| RowVersion | timestamp | Yes |  |  |  |
| IsParkingFeesEnabled | bit | No |  |  |  |
| ParkingFees | decimal | Yes |  |  |  |
| ExternalLoyaltyId | int | Yes |  |  | Identifier/Foreign key |
| ExternalLoyaltyId | int | Yes |  |  | Identifier/Foreign key |
| ExternalLoyaltyId | int | Yes |  |  | Identifier/Foreign key |
| Tolls | decimal | Yes |  |  |  |
| ActualDropOffDate | datetimeoffset | Yes |  |  | Timestamp field |
| ActualDropOffDate | datetimeoffset | Yes |  |  | Timestamp field |
| ActualDropOffDate | datetimeoffset | Yes |  |  | Timestamp field |
| ActualDropOffDate | datetimeoffset | Yes |  |  | Timestamp field |
| ActualDropOffDate | datetimeoffset | Yes |  |  | Timestamp field |
| GraceHoursDenominator | decimal | Yes |  |  |  |
| IsGraceHoursUponOpenContractEnabled | bit | Yes |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| Discriminator | nvarchar | No |  |  |  |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| QuotationId | int | Yes |  |  | Identifier/Foreign key |
| AccidentPolicyId | int | Yes |  |  | Identifier/Foreign key |
| ReasonId | bigint | Yes |  |  | Identifier/Foreign key |
| ReasonId | bigint | Yes |  |  | Identifier/Foreign key |
| ReasonId | bigint | Yes |  |  | Identifier/Foreign key |
| WaitingCompletion | bit | No |  |  |  |
| WaitingCompletion | bit | No |  |  |  |
| WaitingCompletion | bit | No |  |  |  |
| WaitingCompletion | bit | No |  |  |  |
| BranchId | int | No |  |  | Identifier/Foreign key |
| Guid | uniqueidentifier | No |  |  | Identifier/Foreign key |
| FreeHours | int | Yes |  |  |  |
| LeasingQuotationId | int | Yes |  |  | Identifier/Foreign key |
| MonthlyRateAmount | decimal | Yes |  |  | Monetary value |
| EnableClose | bit | Yes |  |  |  |
| EnableClose | bit | Yes |  |  |  |
| EnableClose | bit | Yes |  |  |  |
| DiscountPercentage | decimal | Yes |  |  |  |
| UtilizationRateId | int | Yes |  |  | Identifier/Foreign key |
| AllLineItemsGenerated | bit | No |  |  |  |
| FillingFuelFees | decimal | Yes |  |  |  |
| LeasingRequestId | int | Yes |  |  | Identifier/Foreign key |
| LeasingRequestId | int | Yes |  |  | Identifier/Foreign key |
| LeasingRequestId | int | Yes |  |  | Identifier/Foreign key |
| LeasingRequestId | int | Yes |  |  | Identifier/Foreign key |
| FillingFuelFeesValuePerOneEighth | decimal | Yes |  |  |  |
| TotalPaidAmount | decimal | Yes |  |  | Identifier/Foreign key |
| TotalDueAmount | decimal | Yes |  |  | Monetary value |
| LastLineItemsGeneratedOn | datetime2 | Yes |  |  |  |
| FuelUnitPrice | decimal | Yes |  |  | Monetary value |
| LastFinancialTransactionDate | datetime2 | Yes |  |  | Timestamp field |
| ContractPointsEvaluated | bit | Yes |  |  |  |
| WaivedRepairTasks | nvarchar | Yes |  |  |  |
| HasComments | bit | No |  |  |  |
| HasComments | bit | No |  |  |  |
| HasComments | bit | No |  |  |  |
| OplRequestId | int | Yes |  |  | Identifier/Foreign key |
| IsAdditionalDiscount | bit | Yes |  |  |  |
| InsuranceDeposit | decimal | Yes |  |  |  |
| BrokerId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| BrokerId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| BrokerId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| BrokerId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| CouponCode | nvarchar | Yes |  |  |  |
| ClosedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| ClosedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| ClosedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CreatedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| CloseContractWithoutEarlyReturnPenalty | bit | Yes |  |  |  |
| AccidentPolicyRatioParticipationPercentage | int | Yes |  |  | Identifier/Foreign key |
| InsuranceDepositRatioParticipationPercentage | int | Yes |  |  |  |
| IntegrationStatusId | int | Yes |  |  | Identifier/Foreign key |
| IntegrationStatusId | int | Yes |  |  | Identifier/Foreign key |
| IntegrationStatusId | int | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| AdvancedPaymentRatioParticipationPercentage | int | Yes |  |  |  |
| DisplayCorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| DisplayCorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| DisplayCorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| AuthorizedDriverId | int | Yes |  |  | Identifier/Foreign key |
| EstimatedByUserId | bigint | Yes |  |  | Identifier/Foreign key |
| IsApproachToEndNotified | bit | Yes |  |  |  |
| OutBranchBorderPenalty | decimal | Yes |  |  |  |
| OutCityEstimationAmount | decimal | Yes |  |  | Monetary value |
| OutCityEstimationCityId | int | Yes |  |  | Identifier/Foreign key |
| OutCityEstimationDateTime | datetime2 | Yes |  |  | Timestamp field |
| OutCityEstimationStatusId | bigint | Yes |  |  | Identifier/Foreign key |
| PartialPayment | decimal | Yes |  |  |  |
| SkipEngineAndDoorsStatusCheck | bit | Yes |  |  | Status indicator |
| VehicleLatitudeAtClose | decimal | Yes |  |  |  |
| VehicleLongitudeAtClose | decimal | Yes |  |  |  |
| AllowContractExtension | bit | No |  |  |  |
| HasSignedCommitmentDocument | bit | Yes |  |  |  |
| IsUnAuthorizedContractNotified | bit | Yes |  |  |  |
| BillableCategoryId | int | No |  |  | Identifier/Foreign key |
| IntegrationFees | decimal | Yes |  |  |  |
| FreeCalculationItems | nvarchar | Yes |  |  |  |
| MonthlyFreeHours | int | Yes |  |  |  |
| NextRecurringPaymentDate | datetime2 | Yes |  |  | Timestamp field |
| OriginalActualEndDate | datetimeoffset | Yes |  |  | Timestamp field |
| ApplyLocalRatesOnContract | bit | Yes |  |  |  |
| LocalRateAmount | decimal | Yes |  |  | Monetary value |
| LocalRateCurrencyId | int | Yes |  |  | Identifier/Foreign key |
| SpotContractBase_IsAdditionalDiscount | bit | Yes |  |  |  |

### Rental.Bookings

**Purpose:** Booking patterns and demand signals

| Column | Data Type | Nullable | PK | Identity | Description |
|--------|-----------|----------|----|---------|--------------|
| Id | int | No | ✓ |  | Identifier/Foreign key |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| PickupDate | datetimeoffset | Yes |  |  | Timestamp field |
| PickupDate | datetimeoffset | Yes |  |  | Timestamp field |
| PickupDate | datetimeoffset | Yes |  |  | Timestamp field |
| PickupDate | datetimeoffset | Yes |  |  | Timestamp field |
| DropoffDate | datetimeoffset | Yes |  |  | Timestamp field |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| PickupBranchId | int | No |  |  | Identifier/Foreign key |
| DropoffBranchId | int | No |  |  | Identifier/Foreign key |
| ModelId | int | No |  |  | Identifier/Foreign key |
| ModelId | int | No |  |  | Identifier/Foreign key |
| ModelId | int | No |  |  | Identifier/Foreign key |
| Year | int | No |  |  |  |
| Year | int | No |  |  |  |
| Year | int | No |  |  |  |
| Comment | nvarchar | Yes |  |  |  |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| StatusId | bigint | No |  |  | Identifier/Foreign key |
| RentalRateId | int | Yes |  |  | Identifier/Foreign key |
| SourceId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| TenantId | int | No |  |  | Identifier/Foreign key |
| BookingNumber | nvarchar | No |  |  |  |
| TransferCostId | int | Yes |  |  | Identifier/Foreign key |
| CancelReasonId | bigint | Yes |  |  | Identifier/Foreign key |
| AcceptableTimeToCancel | int | Yes |  |  | Timestamp field |
| RowVersion | timestamp | Yes |  |  |  |
| IsParkingFeesEnabled | bit | Yes |  |  |  |
| ParkingFees | decimal | Yes |  |  |  |
| PenaltyPercentage | float | Yes |  |  |  |
| IsGraceHoursEnabled | bit | Yes |  |  |  |
| DriverId | int | Yes |  |  | Identifier/Foreign key |
| BookingTypeId | bigint | No |  |  | Identifier/Foreign key |
| BookingTypeId | bigint | No |  |  | Identifier/Foreign key |
| BookingTypeId | bigint | No |  |  | Identifier/Foreign key |
| CorporateId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| QuotationId | int | Yes |  |  | Identifier/Foreign key |
| BranchId | int | No |  |  | Identifier/Foreign key |
| Guid | uniqueidentifier | No |  |  | Identifier/Foreign key |
| TotalPaidAmount | decimal | Yes |  |  | Identifier/Foreign key |
| TotalDueAmount | decimal | Yes |  |  | Monetary value |
| IsBookingCustomerNotified | bit | No |  |  |  |
| LastStatusUpdatedBy | bigint | Yes |  |  | Timestamp field |
| LastStatusUpdatedOn | datetimeoffset | Yes |  |  | Timestamp field |
| InternalAuthorizationCost | decimal | Yes |  |  |  |
| IsInternalAuthorizationEnabled | bit | Yes |  |  |  |
| IsInternalAuthorizationFeesAppliedOnBooking | bit | Yes |  |  |  |
| IsParkingFeesAppliedOnBooking | bit | Yes |  |  |  |
| IsAdditionalDiscount | bit | Yes |  |  |  |
| FlightNumber | nvarchar | Yes |  |  |  |
| BrokerId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| BrokerBookingReferenceNumber | nvarchar | Yes |  |  |  |
| CouponCode | nvarchar | Yes |  |  |  |
| IsFullCreditEnabled | bit | Yes |  |  |  |
| TempId | int | Yes |  |  | Identifier/Foreign key |
| TempId2 | int | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| FranchiseId | uniqueidentifier | Yes |  |  | Identifier/Foreign key |
| DurationTypeId | bigint | No |  |  | Identifier/Foreign key |
| VehicleId | int | Yes |  |  | Identifier/Foreign key |
| IsCustomerNotifiedOnUnavailableVehicle | bit | Yes |  |  |  |
| HasDriverAuthorizationBlocker | bit | No |  |  |  |
| ReassignVehicleReasonId | int | Yes |  |  | Identifier/Foreign key |
| IsFailureBeforeBookingExecutionNotified | bit | Yes |  |  |  |
| BillableCategoryId | int | No |  |  | Identifier/Foreign key |
| BrandId | bigint | Yes |  |  | Identifier/Foreign key |
| PaymentTermId | bigint | Yes |  |  | Identifier/Foreign key |
| DriverAuthorizationCountryId | int | Yes |  |  | Identifier/Foreign key |
| DriverAuthorizationPrice | decimal | Yes |  |  | Monetary value |
| DriverAuthorizationTypeId | bigint | Yes |  |  | Identifier/Foreign key |
| BusinessAccountName | nvarchar | Yes |  |  |  |
| BusinessAccountNumber | bigint | Yes |  |  |  |
| CustomerContract | nvarchar | Yes |  |  |  |
| NumberOfDays | int | Yes |  |  |  |
| VoucherValue | float | Yes |  |  |  |
| FreeCalculationItems | nvarchar | Yes |  |  |  |
| IntegrationFees | decimal | Yes |  |  |  |
| AccidentPolicyRatioParticipationPercentage | int | Yes |  |  | Identifier/Foreign key |
| AdvancedPaymentRatioParticipationPercentage | int | Yes |  |  |  |
| InsuranceDepositRatioParticipationPercentage | int | Yes |  |  |  |
| ModeId | bigint | No |  |  | Identifier/Foreign key |
| IsRecurringPaymentAllowed | bit | Yes |  |  |  |
| IsSecretRate | bit | No |  |  |  |
| PurchaseOrder | nvarchar | Yes |  |  |  |

### Rental.RentalRates

**Purpose:** Configured pricing rates

| Column | Data Type | Nullable | PK | Identity | Description |
|--------|-----------|----------|----|---------|--------------|
| Id | int | No | ✓ |  | Identifier/Foreign key |
| CreationTime | datetime2 | No |  |  | Timestamp field |
| CreatorUserId | bigint | Yes |  |  | Identifier/Foreign key |
| LastModificationTime | datetime2 | Yes |  |  | Timestamp field |
| LastModifierUserId | bigint | Yes |  |  | Identifier/Foreign key |
| Start | datetime2 | No |  |  |  |
| CountryId | int | No |  |  | Identifier/Foreign key |
| BranchId | int | Yes |  |  | Identifier/Foreign key |
| ModelId | int | No |  |  | Identifier/Foreign key |
| Year | int | Yes |  |  |  |
| TrimId | int | Yes |  |  | Identifier/Foreign key |
| EngineSize | int | Yes |  |  |  |
| DailyFreeKm | int | Yes |  |  |  |
| HourlyFreeKm | int | Yes |  |  |  |
| ExtraKmCost | decimal | Yes |  |  |  |
| IsActive | bit | No |  |  |  |
| TenantId | int | No |  |  | Identifier/Foreign key |
| SchemaId | int | No |  |  | Identifier/Foreign key |
| RowVersion | timestamp | Yes |  |  |  |
| End | datetime2 | Yes |  |  |  |
| MonthlyFreeKM | int | Yes |  |  |  |
| TypeId | int | No |  |  | Identifier/Foreign key |
| UnlimitedKmEnabled | bit | No |  |  |  |

## 4. Supporting Tables

These tables provide dimensional context and reference data:

- **Fleet.Vehicles** (68 columns): Vehicle master data
- **Fleet.Locations** (31 columns): Fleet locations
- **Rental.Branches** (19 columns): Rental branch information
- **Rental.Cities** (6 columns): City reference data
- **Rental.Countries** (8 columns): Country reference data

## 5. Data Constraints and Assumptions

### Date Filter

- **All data must be from 2023-01-01 onwards**
- Apply this filter to CreationTime, OperationDateTime, or equivalent date columns

### Utilization Calculation

- **Source:** `Fleet.VehicleHistory` ONLY (as per instructions)
- **Method:** Calculate percentage of time vehicles are in 'Rented' status vs. 'Available'
- **Status Mapping:** To be determined from actual data inspection

### Data Quality Assumptions

- Timestamps are in consistent timezone
- StatusId values are consistent and documented in Lookups table
- No data before 2023-01-01 will be used
- Missing values will be handled during data preparation

## 6. Next Steps

1. ✅ **STEP 0-A:** Database dictionary parsed successfully
2. ✅ **STEP 0-B:** Database connection and table discovery
3. ✅ **STEP 0-C:** Data dictionary report generated (this document)
4. ⏭️ **STEP 0-D:** Create initial training dataset from key tables
5. ⏭️ **STEP 0-E:** Fetch external data (KSA holidays, events)
6. ⏭️ **STEP 0-F:** Merge external signals with training data
7. ⏭️ **STEP 0-G:** Document data understanding and decisions

---

*This document is automatically generated and should be updated as the project evolves.*

# Data Discovery Report - CHUNK 1

**Generated:** 2025-05-31 (Simulated Date)  
**Project:** Dynamic Pricing Tool for Renty SaaS  
**MVP Tenant:** YELO  
**Database:** eJarDbSTGLite (SQL Server, Windows Authentication)

---

## 1. Executive Summary

### Key Findings
- **YELO Tenant ID:** `1` (Name: 'Yelo', TenancyName: 'Default')
- **Total Contracts (2022+):** 3,152,274
- **Individual Rentals (Discriminator='Contract'):** 2,826,983
- **Data Range:** 2022-01-01 to 2025-11-18
- **Active Branches:** 168
- **Car Models:** 485
- **Top 6 Categories Already Defined:** Yes (in `dynamicpricing.TopCategories`)
- **Top 6 Branches Already Defined:** Yes (in `dynamicpricing.TopBranches`)
- **Pre-existing Training Data:** 36,308 records
- **Pre-existing Validation Data:** 4,749 records

---

## 2. Database Architecture

### 2.1 Key Schemas
| Schema | Purpose |
|--------|---------|
| `dbo` | Core ABP framework tables (AbpTenants, Lookups) |
| `Rental` | Main rental operations (Contract, Branches, CarModels, RentalRates) |
| `Fleet` | Vehicle management (Vehicles, CarCategories) |
| `dynamicpricing` | **Pre-existing tables for our tool!** |

### 2.2 Pre-existing dynamicpricing Schema
The `dynamicpricing` schema already exists with 4 tables:
- `dynamicpricing.TopBranches` - 6 rows (MVP branches selected)
- `dynamicpricing.TopCategories` - 6 rows (MVP categories selected)
- `dynamicpricing.TrainingData` - 36,308 rows (structure: RentalDate, BranchId, CategoryId, Demand, AvgBasePrice)
- `dynamicpricing.ValidationData` - 4,749 rows (same structure)

---

## 3. YELO Tenant Data

### 3.1 Tenant Identification
```sql
-- YELO Tenant
Id: 1
Name: 'Yelo'
TenancyName: 'Default'
IsActive: True
IsDeleted: False
```

### 3.2 Contract Types (Discriminator Values)
| Discriminator | Count (2022+) | Use for Training |
|---------------|---------------|------------------|
| Contract | 2,826,983 | ✅ Yes (Individual Rentals) |
| BrokerContract | 262,342 | ❌ No |
| CorporateContract | 47,300 | ❌ No |
| LeasingContract | 14,197 | ❌ No |
| MonthlyContract | 1,412 | ❌ No |
| OplContract | 40 | ❌ No |

### 3.3 Contract Status Distribution
| StatusId | Status | Count | Include |
|----------|--------|-------|---------|
| 211 | Delivered | 3,027,058 | ✅ Yes |
| 212 | Cancelled | 105,560 | ❌ No |
| 210 | Open | 19,649 | ❌ No |
| 213 | Paused | 7 | ❌ No |

**Training Filter:** `Discriminator = 'Contract' AND StatusId = 211`

---

## 4. MVP Scope Data

### 4.1 Top 6 Branches (Pre-defined in dynamicpricing.TopBranches)
| BranchId | Branch Name | Type |
|----------|-------------|------|
| 122 | King Khalid Airport Terminal 5 - Riyadh | Airport |
| 15 | King Abdulaziz Airport Terminal 1 - Jeddah | Airport |
| 26 | Abha Airport | Airport |
| 34 | Al Khaldiyah - Al Madina | City |
| 2 | Al Quds - Riyadh | City |
| 211 | Al Yarmuk - Riyadh | City |

### 4.2 Top 6 Categories (Pre-defined in dynamicpricing.TopCategories)
| CategoryId | Category Name |
|------------|---------------|
| 27 | Compact |
| 2 | Small Sedan |
| 3 | Intermediate Sedan |
| 29 | Economy SUV |
| 13 | Intermediate SUV |
| 1 | Economy |

### 4.3 Rental Volume by Top Categories (2022+)
| CategoryId | Category | Rental Count |
|------------|----------|--------------|
| 27 | Compact | 1,076,953 |
| 2 | Small Sedan | 885,332 |
| 3 | Intermediate Sedan | 301,115 |
| 29 | Economy SUV | 153,515 |
| 13 | Intermediate SUV | 50,016 |
| 1 | Economy | 44,301 |

---

## 5. Key Tables and Relationships

### 5.1 Primary Tables for Dynamic Pricing

#### Rental.Contract
```
- Id (int, PK)
- TenantId (int) → Filter: 1 (YELO)
- Discriminator (nvarchar) → Filter: 'Contract'
- StatusId (bigint) → Filter: 211 (Delivered)
- PickupBranchId (int) → FK to Rental.Branches
- VehicleId (int) → FK to Fleet.Vehicles
- Start (datetimeoffset) → Rental start date
- End (datetimeoffset) → Rental end date
- ActualDropOffDate (datetimeoffset)
- DailyRateAmount (decimal) → Base daily price
- RentalRateId (int) → FK to Rental.RentalRates
- BookingId (int) → FK to Rental.Bookings
```

#### Rental.ContractsPaymentsItemsDetails
```
- Id (int, PK)
- ContractId (int) → FK to Rental.Contract
- ItemTypeId (int) → 1 = "Trip Days" (base rental price)
- ItemName (nvarchar)
- Quantity (decimal) → Number of days
- UnitPrice (decimal) → Daily rate
- TotalPrice (decimal)
- DiscountPct (real)
```

**Key ItemTypeIds:**
- `1` = Trip Days (Base Rental - USE THIS)
- `2` = Hours
- `4` = Fuel Cost
- `6` = Extra Km
- `9` = Yelo Shield
- `10` = Yelo Shield Plus

#### Rental.Branches
```
- Id (int, PK)
- Name (nvarchar, JSON with en/ar)
- TenantId (int)
- CityId (int) → FK to Rental.Cities
- IsAirport (bit)
- IsActive (bit)
```

#### Rental.CarModels
```
- Id (int, PK)
- ModelId (int)
- CarModelName (nvarchar, JSON)
- CarCategoryId (int)
- CarCategoryName (nvarchar, JSON)
- TenantId (int)
```

#### Fleet.Vehicles
```
- Id (int, PK)
- ModelId (int) → FK to Rental.CarModels.ModelId
- TenantId (int)
- BranchId (int)
- StatusId (int)
```

### 5.2 Join Strategy for Training Data Extraction
```sql
SELECT 
    CONVERT(DATE, c.Start) as RentalDate,
    c.PickupBranchId as BranchId,
    cm.CarCategoryId as CategoryId,
    COUNT(*) as Demand,
    AVG(c.DailyRateAmount) as AvgBasePrice
FROM Rental.Contract c
INNER JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
WHERE c.TenantId = 1
  AND c.Discriminator = 'Contract'
  AND c.StatusId = 211
  AND c.Start >= '2022-01-01'
  AND c.PickupBranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
  AND cm.CarCategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
GROUP BY CONVERT(DATE, c.Start), c.PickupBranchId, cm.CarCategoryId
```

---

## 6. Data Quality Assessment

### 6.1 DailyRateAmount Completeness
| Metric | Value |
|--------|-------|
| Contracts with DailyRateAmount > 0 | 2,723,350 (100%) |
| Contracts with RentalRateId | 2,723,350 (100%) |
| Min DailyRateAmount | 15.00 SAR |
| Max DailyRateAmount | 19,250.00 SAR |
| Avg DailyRateAmount | 234.07 SAR |

### 6.2 Monthly Rental Volume (2023-2025)
Data is consistent with ~55,000-70,000 individual rentals per month.

---

## 7. Date Ranges

### 7.1 Training Period
- **Start:** 2022-01-01
- **End:** 2025-05-31 (simulated today)
- **Total Days:** ~1,246 days

### 7.2 Validation Period
- **Start:** 2025-06-01
- **End:** 2025-11-18 (max data available)
- **Total Days:** ~171 days

---

## 8. Schema to Create: appconfig

Per instructions, we need to create the `appconfig` schema in `eJarDbSTGLite` for:
- Model parameters
- Feature configurations
- ML model metadata
- Pricing rules

---

## 9. Recommendations for CHUNK 2

1. **Use Pre-existing dynamicpricing Schema:** The schema already exists with TopBranches, TopCategories, TrainingData, and ValidationData tables.

2. **Data Extraction Query:** Use the join strategy documented above to refresh training data.

3. **Base Price Source:** Use `Contract.DailyRateAmount` directly (100% complete) instead of parsing ContractsPaymentsItemsDetails.

4. **Weather Integration:** Need to map branch cities to coordinates for Open-Meteo API.

5. **Holiday Calendar:** Use KSA holidays from Calendarific API for feature engineering.

---

## 10. SQL Server Connection Configuration

```python
# Windows Authentication (Local)
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)
```

---

## Appendix A: Schema Listing

Schemas in eJarDbSTGLite:
- Archive, Cache, Collections, Compare, ConfigurationManagement, Crm
- dbo, dynamicpricing, Finance, Fleet, guest
- Migration, MultiTenancy, Rental, Reporting
- Workflows

---

**Document Version:** 1.0  
**Author:** Dynamic Pricing Tool - Automated Discovery  
**CHUNK:** 1 - SQL Server Data Discovery

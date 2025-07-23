# Trading System Workspace Overview

This workspace contains a sophisticated algorithmic trading system with NinjaTrader 8 integration and multiple backend microservices.

## Current Session Model
- **Model**: Sonnet 4 (claude-sonnet-4-20250514)
- **Updated**: 2025-07-15
- **Fixed**: Windows compatibility for startup menus (storage-menu.js, risk-menu.js)

## Critical LanceDB Behavior
- **Schema Initialization**: When storage agent starts with 0 vectors, must create a blank/dummy record
- **Requirement**: One row must exist in LanceDB table before additional records can be stored
- **Current Implementation**: Creates SCHEMA_INIT record, then deletes it after schema setup
- **Potential Issue**: May need to keep dummy record instead of deleting it

## Critical Trade Storage Issue (2025-07-15)
- **Problem**: Trade classifier marking all trades as "Too low importance (0%)"
- **Result**: All trades being skipped with message "🗑️ SKIPPED: [ID] - Too low importance (0%)"
- **Impact**: No trade data being stored despite valid payloads from NinjaTrader
- **Debug Data**: Shows valid features (74 count), outcomes (PnL: 45), but shouldStore: false
- **Fix Needed**: Investigate trade classifier logic or set FORCE_STORE_ALL flag

## GP Training Data Issues (2025-07-15)
- **Issue 1**: GP trainer expects specific filename format (e.g., "MGC_long_training.json")
- **Issue 2**: Data format mismatch - trainer expects structured format vs array of records
- **Issue 3**: Filename normalization - "MGC AUG25" vs "MGC"
- **Solutions Applied**:
  - ✅ Updated export to create properly named files by instrument+direction
  - ✅ Added convertToGPFormat() to transform Storage Agent data to GP trainer format
  - ✅ Added normalizeInstrumentName() to strip contract suffixes (AUG25, SEP25, etc.)
  - ✅ Fixed Windows ENOBUFS with Node.js HTTP instead of curl
- **Current Status**: Export works, files created with correct format and names

## Project Structure

### Frontend: order-manager/
- **Purpose**: NinjaTrader 8 trading application
- **Focus Areas**: Order execution, position management, signal integration
- **Note**: Contains various NinjaTrader indicators, strategies, and utilities
- **Git Repository**: Separate git repo for NinjaTrader code

### Backend: production-curves/
- **Purpose**: Microservices architecture for market analysis and signal generation
- **Location**: Most services are in the `Production/` subdirectory
- **Note**: Contains many test files, experimental code, and development artifacts - focus on core service directories
- **Git Repository**: Separate git repo for backend services

## Key Microservices (in Production/)

### 1. Market Ingestion Service (mi-service/)
- **Port**: 3002
- **Purpose**: Real-time market data processing
- **Key Files**:
  - `server.js` - Main service entry
  - `src/ingestion/` - Core ingestion logic
  - `/api/bars/{instrument}` - Bar buffer API
  - `/api/ingest/rf-buffer/{instrument}` - RF-specific data endpoint

### 2. Matching Engine Service (me-service/)
- **Port**: 5000
- **Purpose**: Pattern matching and IBI signal generation
- **Key Files**:
  - `server.js` - Main service entry
  - `src/matching/` - Pattern matching algorithms
  - `src/ibi/` - Instrument Behavior Intelligence
- **Modes**: Traditional, IBI-only, or hybrid

### 3. Random Forest Service (rf-service/)
- **Port**: 3009
- **Purpose**: ML ensemble predictions with bracket voting
- **Key Files**:
  - `server.js` - Express server with prediction endpoints
  - `src/bridge/pytorch-bridge.js` - Node-Python bridge
  - `src/pytorch-predictor/enhanced_pytorch_server.py` - Model inference
- **Models**: 3-model pipeline (Direction, TradeManager, Statistical Validator)

### 4. Signal Pool Service (signal-pool/)
- **Port**: 3004
- **Purpose**: Central signal aggregation and distribution
- **Key Files**:
  - `server.js` - Main service
  - Signal clustering and scoring logic

### 5. Forecasting Service (forecasting-service/)
- **Port**: 3003
- **Purpose**: 3-bar price predictions
- **Note**: Advanced pattern detection and volatility analysis

### 6. Kalman Fusion Service (kalman-fusion/)
- **Port**: 3005
- **Purpose**: Adaptive signal fusion with Thompson feedback
- **Note**: Meta-signal generation

## Important Considerations

### Working with the Codebase
1. **Test File Clutter**: Each service directory contains numerous test files, debug scripts, and experimental code. Focus on:
   - `server.js` or `index.js` as entry points
   - `src/` directories for core logic
   - Ignore `test/`, `debug/`, `experimental/` folders initially

2. **Configuration**: Services use environment variables extensively. Look for:
   - `.env` files (if present)
   - Environment variable documentation in service README files
   - Default configurations in service entry files

3. **Data Flow Priority**:
   ```
   Market Data → MI Service → ME/RF Services → Signal Pool → NinjaTrader
   ```

### RF Training Resources
- **Location**: `production-curves/Production/rf-training/`
- **Purpose**: Model development and training
- **Note**: Separate from production services, contains many experimental scripts

## Development Focus Areas

### For Trading Logic:
- `order-manager/` - NinjaTrader strategies and indicators
- `production-curves/Production/me-service/src/ibi/` - IBI entry conditions

### For ML/Predictions:
- `production-curves/Production/rf-service/` - Live inference
- `production-curves/Production/rf-training/scripts/core/` - Model training

### For Market Data:
- `production-curves/Production/mi-service/` - Data ingestion and processing

### For Signal Management:
- `production-curves/Production/signal-pool/` - Signal aggregation

## Quick Start Commands

```bash
# Navigate to production services
cd production-curves/Production/

# Start a specific service (example)
cd mi-service && npm start

# View RF service logs
cd rf-service && tail -f logs/rf-service.log
```

## Architecture Documents
- Master Architecture: `/mnt/c/Users/aport/Documents/Production_Curves/Architecture/master-architecture.md`
- RF Architecture: `/mnt/c/Users/aport/Documents/Production_Curves/Architecture/rf-architecture.md`

## Development Standards (Adapted from Cursor Rules)

### Implementation Protocol
- **Systematic Code Protocol**: Analysis → Planning → Incremental Changes → Testing
- **Modularity First**: Break complex logic into atomic parts, prefer importing over modifying
- **File Management**: Keep files under 500 lines, organize into directories
- **Dependency Analysis**: Always analyze cascading effects before changes
- **Preserve What Works**: Don't modify working components unnecessarily
- **No Synthetic Data**: Don't implement fallbacks that hide mistakes

### Interaction Standards
- **Confirmations Required**: Always confirm what files/changes are being made
- **Clarification First**: Ask detailed questions, remove ambiguities
- **Step-by-Step Reasoning**: Break down problems, evaluate trade-offs
- **Windows Environment**: Use PowerShell, separate commands with `;`
- **Server Management**: Don't start servers unless explicitly requested
- **Logging Standards**: Unless user asks to log to file, assume "log" means terminal print/console output

### Testing & Debugging
- **Proactive Testing**: Test code accompanies functionality
- **Dependency-Based Testing**: Test all affected components
- **No Breakage Assertion**: Verify changes don't break existing functionality
- **Debugging Protocol**: Diagnose → Observe → Reason → Fix

## Planning and Documentation Requirements
- **Keep hard files in workspace/ for /plan references**
- Planning documents should be stored as physical files to persist across Claude Code sessions
- Use workspace/ directory for any planning materials that need to survive Claude Code restarts
- All session plans and task lists should be maintained in workspace/ files
- **Thought Track Record**: @claude_memory.md - Chronological development thoughts and changes

## Strategic Evolution: RF → Agentic Memory System

### Historical Context: RF Meta-Labeling Pipeline (IMPLEMENTED)
Previously implemented complete meta-labeling approach where traditional strategies provide the "edge" and ML models enhance signal filtering. This addressed the poor performance (~10% accuracy) of pure pattern discovery approaches.

**Previous Architecture Flow:**
```
Traditional Strategy → BuildNewSignal() → RF Filter (Optional) → Signal Approval Service → Entry/Exit → Training Data Export
```

### Current Direction: Agentic Memory System (IMPLEMENTED)
Successfully transitioned from static RF models to adaptive agentic memory that learns optimal risk parameters from historical patterns using graduated feature matching.

**Implemented Architecture Flow:**
```
NT → MI (bars) → ME (94+ features) → Risk Agent (graduated features) → Storage Agent
                                   ↓
Position Exit → ME → Storage (full 94 features) → LanceDB → Graduated Similarity → Risk Decisions
```

### Key Architectural Breakthrough
- **From**: Static ML filtering with fixed risk parameters and full vector comparison
- **To**: Adaptive risk management with graduated feature similarity learning from historical outcomes
- **Innovation**: Feature-specific similarity matching instead of full vector comparison
- **Location**: `production-curves/Production/agentic_memory/`
- **Status**: ✅ **OPERATIONAL** (2025-07-10)

### Agentic Memory Components (Phase 1 - COMPLETED)

#### 1. Storage Agent Service ✅
- **Location**: `production-curves/Production/agentic_memory/storage-agent/`
- **Purpose**: LanceDB vector storage with graduated feature similarity matching
- **Technology**: Node.js + Express + LanceDB
- **Key Features**:
  - Graduated feature extraction from stored vectors
  - Feature-by-feature similarity calculation
  - Percentage-based similarity scoring
- **Status**: ✅ **OPERATIONAL**

#### 2. Feature Graduation System ✅
- **Location**: `production-curves/Production/agentic_memory/risk-service/featureGraduation.js`
- **Purpose**: Dynamic feature importance analysis and graduation
- **Technology**: Node.js correlation analysis with PnL outcomes
- **Key Features**:
  - Correlation-based feature scoring (70% weight)
  - Stability analysis (30% weight) 
  - Automatic updates every 30 minutes
  - Domain-knowledge bootstrap with 10 initial features
- **Status**: ✅ **OPERATIONAL**

#### 3. Risk Management Agent ✅
- **Location**: `production-curves/Production/agentic_memory/risk-service/`
- **Purpose**: Calculate optimal SL/TP from similar graduated feature patterns
- **Technology**: Node.js + Graduated LanceDB queries
- **Key Features**:
  - Graduated feature matching instead of full vectors
  - Smart similarity thresholds
  - Continuous learning integration
- **Status**: ✅ **OPERATIONAL**

### Legacy RF Components (Maintained)

#### 1. Signal Tracking Enhancement
- **File**: `order-manager/SharedCustomClasses.cs`
- **Added**: signalType, signalDefinition, confidence fields to patternFunctionResponse
- **Purpose**: Track WHY signals fired for better training data

#### 2. RF Filtering Integration (Optional)
- **File**: `order-manager/MainStrategy.cs:1396-1415`
- **Purpose**: Optional ML filtering after traditional signal generation
- **Parameters**: EnableRFFiltering, RFConfidenceThreshold, MLMode
- **Status**: Available but transitioning to Agentic Memory

#### 3. Traditional Strategy Library
- **File**: `order-manager/TraditionalStrategies.cs`
- **Implemented**: ORDER_FLOW_IMBALANCE with sophisticated wick analysis
- **Features**: 15 new ML features for 1-minute gold volatility
- **Focus**: Buy/sell pressure detection through volume delta and wick patterns

#### 4. External Signal Approval System
- **Files**: 
  - `order-manager/SignalApprovalClient.cs` - HTTP client
  - `production-curves/Production/rf-service/server.js` - Approval endpoint
- **Purpose**: Keep ML filtering logic outside NinjaTrader
- **Design**: Fail-safe (rejects on errors), 5-second timeout

#### 5. Training Data Collection
- **File**: `order-manager/OrderLiteActions.cs:121`
- **Fix**: Resolved null builtSignal preventing training data export
- **Method**: File-based export using existing ConfigManager patterns

### Traditional Strategies for Meta-Labeling

#### ORDER_FLOW_IMBALANCE (Enhanced for 1-Min Gold)
- **Volume Delta**: Calculated using wick analysis vs traditional candlesticks
- **Wick Features**: upperWickRatio, lowerWickRatio, wickImbalance, bodyRatio
- **Context Filtering**: EMA trend alignment, chop detection
- **Scoring**: Cumulative wick scores with decay factors
- **Purpose**: Detect aggressive buying/selling in volatile gold markets

#### Future Strategies (Planned)
- EMA crossover with volume confirmation
- RSI divergence with trend filter
- VWAP mean reversion with momentum
- Breakout patterns with volume validation

### Configuration Parameters

#### RF Filtering Control
```csharp
EnableRFFiltering = false;           // Master switch for ML filtering
RFConfidenceThreshold = 0.6;         // Minimum confidence for signal approval  
MLMode = MLFilterMode.MetaLabeling;  // Meta-labeling vs discovery mode
CollectTrainingData = false;         // Training data export control
```

#### Signal Approval Service
- **Endpoint**: `POST http://localhost:3009/api/approve-signal`
- **Fallback**: Basic risk management when ML models unavailable
- **Response**: Approval boolean, confidence score, reasoning

### Current Development Status
- ✅ All 6 RF implementation phases complete (legacy maintained)
- ✅ Enhanced order flow analysis for 1-minute gold ready
- ✅ External signal approval system operational
- ✅ Training data collection bug fixed
- ✅ **COMPLETED**: Range-Based Agentic Memory System (REVOLUTIONARY)
- ✅ **OPERATIONAL**: Predictive range intelligence with bar time-based updates
- 🎯 **BREAKTHROUGH**: Range-based confidence scoring instead of similarity matching

### Major Implementation Milestone (2025-07-13)

#### Range-Based Intelligence Revolution
**SOLVED THE CORE PROBLEM**: Transformed from meaningless similarity matching to predictive range intelligence:

**Old Similarity Approach (FAILED)**:
- Compare feature vectors for "similarity"
- 99.9% similarity but random outcomes
- Constant features create false matches
- No understanding of what leads to profits

**New Range-Based Approach (REVOLUTIONARY)**:
- **Optimal ranges** from profitable trades (Q25-Q75)
- **Acceptable ranges** from profitable trades (P10-P90)
- **Confidence scoring** based on how query fits ranges
- **Signal direction** understanding (higher/lower is better)

**Example Range Analysis**:
```
Query: atr_percentage = 0.2 (from NinjaTrader)
MGC Long Optimal Range: 0.019 - 0.034  
Result: POOR confidence (10%) - 6-10x higher than profitable range!
Action: Correctly rejects high-volatility conditions
```

#### Intelligent Range-Based Graduation
**Profitable trade analysis** replaces similarity:
- **Range Calculation**: Q25-Q75 for optimal, P10-P90 for acceptable
- **Signal Direction**: Compare profitable vs unprofitable means
- **Bar Time Updates**: Every 30 minutes based on actual trade timestamps
- **Contract Normalization**: MGC tables work across all MGC contracts
- **Statistical Significance**: Requires minimum data for reliable ranges

#### Revolutionary Confidence System
**Range-based confidence scoring**:
- **OPTIMAL** (0.8-1.0): Query within Q25-Q75 of profitable trades
- **ACCEPTABLE** (0.4-0.8): Query within P10-P90 of profitable trades  
- **POOR** (0.1-0.4): Query outside acceptable ranges
- **Rejection Logic**: 3+ poor features = reject trade
- **Market Intelligence**: Knows MGC long prefers low volatility

#### Critical Discovery: What MGC Long Profits Require
- **Low volatility** (atr_percentage: 0.019-0.034 vs 0.2 query)
- **Calm markets** (atr_14: 0.544-0.938 vs 5.5 query)
- **No inside bars** (inside_bar = 0 preferred)
- **Normal price efficiency** (high_low_ratio: 1.0002-1.0008)

### Session Logging
This document maintains session continuity for Claude Code interactions. Key developments:
- **2025-01-10**: Designed Agentic Memory system architecture
- **2025-01-10**: Moved agentic_memory to production-curves/Production/ for git integration
- **2025-07-10**: **MAJOR MILESTONE** - Completed graduated feature matching implementation
- **2025-07-10**: Fixed ME feature generation pipeline (14 → 94+ features)
- **2025-07-10**: Implemented intelligent similarity matching with feature graduation
- **2025-07-13**: **REVOLUTIONARY BREAKTHROUGH** - Range-based graduation system
- **2025-07-13**: Solved similarity matching problems with profitable range intelligence
- **2025-07-13**: Implemented bar time-based graduation updates (30-minute intervals)
- **2025-07-13**: **MAJOR MILESTONE** - Complete Gaussian Process migration implementation
- **2025-07-15**: Fixed profitByBar trajectory data flow from NinjaTrader to Storage Agent
- **2025-07-17**: **CRITICAL FIX** - Normalized all PnL calculations to per-contract values

## Critical Implementation Details

### Position Size Normalization (2025-07-17)
**CRITICAL**: All PnL calculations must use normalized per-contract values:
- **Storage**: Stores both `pnl` (raw) and `pnlPerContract` (normalized)
- **Risk Calculations**: Use `pnlPerContract || pnl` pattern for backward compatibility
- **Pattern Matching**: Compare trades fairly regardless of position size
- **Graduation Tables**: Separate profitable/unprofitable using per-contract values
- **Heat Maps**: Filter patterns based on normalized thresholds

### Key Code Patterns
```javascript
// Always use this pattern for PnL access:
const normalizedPnl = pattern.pnlPerContract || pattern.pnl || 0;

// For filtering profitable trades:
const profitable = vectors.filter(v => (v.pnlPerContract || v.pnl) > 0);

// For loss calculations:
const avgLoss = patterns.reduce((sum, p) => sum + Math.abs(p.pnlPerContract || p.pnl || 0), 0) / patterns.length;
```

## Notes
- Services communicate via HTTP REST APIs
- Each service can run independently for testing
- Focus on core service files; ignore test/debug directories initially
- The system supports multiple operation modes (traditional, IBI-only, hybrid)
- **EVOLUTION**: From RF meta-labeling to adaptive agentic memory with dynamic risk management
- **NEW LOCATION**: Agentic Memory development in `production-curves/Production/agentic_memory/`
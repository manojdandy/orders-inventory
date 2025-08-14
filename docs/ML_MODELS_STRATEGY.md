# 🎯 ML Models Strategy & Implementation

## Detailed Machine Learning Model Recommendations

---

## 🔮 **1. Demand Forecasting Models**

### **Model Types & Use Cases:**

#### **A. Time Series Forecasting**
```python
# LSTM for Complex Patterns
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

class DemandForecaster:
    def __init__(self, lookback_window=30):
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(lookback_window, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
    
    def train(self, X_train, y_train):
        self.model.compile(optimizer='adam', loss='mse')
        return self.model.fit(X_train, y_train, batch_size=32, epochs=100)
```

#### **B. Prophet for Seasonal Patterns**
```python
# Facebook Prophet for Business Forecasting
from prophet import Prophet
import pandas as pd

class SeasonalDemandPredictor:
    def __init__(self):
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )
    
    def prepare_data(self, df):
        # Convert to Prophet format
        prophet_df = df.rename(columns={
            'date': 'ds',
            'demand': 'y'
        })
        return prophet_df
    
    def forecast(self, periods=30):
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

#### **C. XGBoost for Feature-Rich Forecasting**
```python
# Gradient Boosting for Complex Feature Engineering
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

class FeatureEnhancedForecaster:
    def __init__(self):
        self.model = xgb.XGBRegressor(
            n_estimators=1000,
            max_depth=6,
            learning_rate=0.01,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
    
    def create_features(self, df):
        """Engineer time-based and lag features"""
        df['dayofweek'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)
        
        # Lag features
        for lag in [1, 7, 14, 30]:
            df[f'demand_lag_{lag}'] = df['demand'].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'demand_rolling_mean_{window}'] = df['demand'].rolling(window).mean()
            df[f'demand_rolling_std_{window}'] = df['demand'].rolling(window).std()
        
        return df.dropna()
```

### **Data Requirements:**
```python
# Minimum data for effective forecasting
{
    "historical_period": "12-24 months",
    "data_frequency": "daily",
    "minimum_records": 365,
    "required_features": [
        "date", "product_id", "quantity_sold",
        "price", "promotions", "seasonality_indicators"
    ],
    "external_factors": [
        "holidays", "weather", "economic_indicators",
        "competitor_actions", "marketing_campaigns"
    ]
}
```

---

## 🎯 **2. Customer Behavior Analytics**

### **A. Customer Segmentation (RFM + Advanced)**
```python
# RFM Analysis with ML Enhancement
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class CustomerSegmentation:
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)
    
    def calculate_rfm(self, orders_df):
        """Calculate Recency, Frequency, Monetary values"""
        current_date = orders_df['order_date'].max()
        
        rfm = orders_df.groupby('customer_id').agg({
            'order_date': lambda x: (current_date - x.max()).days,  # Recency
            'order_id': 'count',  # Frequency
            'total_amount': 'sum'  # Monetary
        }).rename(columns={
            'order_date': 'recency',
            'order_id': 'frequency',
            'total_amount': 'monetary'
        })
        
        return rfm
    
    def advanced_features(self, rfm_df, orders_df):
        """Add behavioral features beyond RFM"""
        # Average order value
        rfm_df['avg_order_value'] = rfm_df['monetary'] / rfm_df['frequency']
        
        # Order patterns
        customer_patterns = orders_df.groupby('customer_id').agg({
            'days_between_orders': 'mean',
            'preferred_category': lambda x: x.mode().iloc[0],
            'price_sensitivity': lambda x: x.std(),
            'seasonal_preference': lambda x: self._get_seasonal_pattern(x)
        })
        
        return rfm_df.join(customer_patterns)
    
    def segment_customers(self, enhanced_rfm):
        """Create customer segments using ML"""
        features = ['recency', 'frequency', 'monetary', 'avg_order_value']
        X_scaled = self.scaler.fit_transform(enhanced_rfm[features])
        
        clusters = self.kmeans.fit_predict(X_scaled)
        enhanced_rfm['segment'] = clusters
        
        # Interpret segments
        segment_names = {
            0: 'Champions',
            1: 'Loyal Customers',
            2: 'Potential Loyalists',
            3: 'At Risk',
            4: 'Lost Customers'
        }
        
        enhanced_rfm['segment_name'] = enhanced_rfm['segment'].map(segment_names)
        return enhanced_rfm
```

### **B. Customer Lifetime Value (CLV) Prediction**
```python
# Predictive CLV using ML
from lifetimes import BetaGeoFitter, GammaGammaFitter
import numpy as np

class CLVPredictor:
    def __init__(self):
        self.bgf = BetaGeoFitter(penalizer_coef=0.0)
        self.ggf = GammaGammaFitter(penalizer_coef=0.0)
    
    def prepare_clv_data(self, orders_df):
        """Prepare data for CLV modeling"""
        from lifetimes.utils import summary_data_from_transaction_data
        
        clv_data = summary_data_from_transaction_data(
            orders_df,
            'customer_id',
            'order_date',
            'total_amount',
            observation_period_end='2023-12-31'
        )
        
        return clv_data
    
    def predict_clv(self, clv_data, periods=12):
        """Predict customer lifetime value"""
        # Fit models
        self.bgf.fit(clv_data['frequency'], clv_data['recency'], clv_data['T'])
        
        # Filter customers with repeat purchases for monetary model
        returning_customers = clv_data[clv_data['frequency'] > 0]
        self.ggf.fit(returning_customers['frequency'], 
                     returning_customers['monetary_value'])
        
        # Predict future transactions
        clv_data['predicted_purchases'] = self.bgf.predict(
            periods, clv_data['frequency'], clv_data['recency'], clv_data['T']
        )
        
        # Predict average order value
        clv_data['predicted_avg_order'] = self.ggf.conditional_expected_average_profit(
            clv_data['frequency'], clv_data['monetary_value']
        )
        
        # Calculate CLV
        clv_data['predicted_clv'] = (clv_data['predicted_purchases'] * 
                                   clv_data['predicted_avg_order'])
        
        return clv_data
```

### **C. Churn Prediction**
```python
# Churn prediction with feature engineering
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd

class ChurnPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            random_state=42
        )
    
    def engineer_churn_features(self, orders_df, customers_df):
        """Create features predictive of churn"""
        current_date = pd.Timestamp.now()
        
        # Recency features
        last_order = orders_df.groupby('customer_id')['order_date'].max()
        days_since_last_order = (current_date - last_order).dt.days
        
        # Frequency features
        order_frequency = orders_df.groupby('customer_id').size()
        avg_days_between_orders = orders_df.groupby('customer_id')['order_date'].apply(
            lambda x: x.diff().dt.days.mean()
        )
        
        # Monetary features
        total_spent = orders_df.groupby('customer_id')['total_amount'].sum()
        avg_order_value = orders_df.groupby('customer_id')['total_amount'].mean()
        
        # Trend features
        recent_orders = orders_df[orders_df['order_date'] >= (current_date - pd.Timedelta(days=90))]
        recent_frequency = recent_orders.groupby('customer_id').size().fillna(0)
        
        # Combine features
        features_df = pd.DataFrame({
            'days_since_last_order': days_since_last_order,
            'total_orders': order_frequency,
            'avg_days_between_orders': avg_days_between_orders,
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'recent_orders_90d': recent_frequency
        }).fillna(0)
        
        # Define churn (no order in last 90 days)
        features_df['is_churned'] = (features_df['days_since_last_order'] > 90).astype(int)
        
        return features_df
    
    def train_churn_model(self, features_df):
        """Train churn prediction model"""
        feature_cols = [col for col in features_df.columns if col != 'is_churned']
        X = features_df[feature_cols]
        y = features_df['is_churned']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.model.fit(X_train, y_train)
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return feature_importance, self.model.score(X_test, y_test)
```

---

## 🛒 **3. Product Recommendation Engine**

### **A. Collaborative Filtering**
```python
# Matrix Factorization for Recommendations
from sklearn.decomposition import NMF
import numpy as np
import pandas as pd

class CollaborativeRecommender:
    def __init__(self, n_components=50):
        self.model = NMF(n_components=n_components, random_state=42)
        self.user_item_matrix = None
        self.user_encoder = None
        self.item_encoder = None
    
    def create_user_item_matrix(self, orders_df):
        """Create user-item interaction matrix"""
        # Create interaction matrix
        interactions = orders_df.groupby(['customer_id', 'product_id'])['quantity'].sum().reset_index()
        
        # Create pivot table
        self.user_item_matrix = interactions.pivot(
            index='customer_id', 
            columns='product_id', 
            values='quantity'
        ).fillna(0)
        
        return self.user_item_matrix
    
    def fit(self, user_item_matrix):
        """Train collaborative filtering model"""
        self.W = self.model.fit_transform(user_item_matrix)
        self.H = self.model.components_
        
        # Reconstruct user-item matrix
        self.predicted_matrix = np.dot(self.W, self.H)
        
    def recommend_products(self, customer_id, n_recommendations=5):
        """Get product recommendations for a customer"""
        if customer_id not in self.user_item_matrix.index:
            return self._recommend_popular_products(n_recommendations)
        
        customer_idx = self.user_item_matrix.index.get_loc(customer_id)
        customer_predictions = self.predicted_matrix[customer_idx]
        
        # Get products not already purchased
        purchased_products = self.user_item_matrix.loc[customer_id]
        not_purchased = purchased_products[purchased_products == 0].index
        
        # Get top recommendations
        product_scores = pd.Series(
            customer_predictions, 
            index=self.user_item_matrix.columns
        )
        
        recommendations = product_scores[not_purchased].nlargest(n_recommendations)
        return recommendations.index.tolist()
```

### **B. Content-Based Filtering**
```python
# Content-based recommendations using product features
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.similarity_matrix = None
        self.products_df = None
    
    def prepare_product_features(self, products_df):
        """Prepare product features for content-based filtering"""
        self.products_df = products_df.copy()
        
        # Combine text features
        self.products_df['combined_features'] = (
            self.products_df['name'].fillna('') + ' ' +
            self.products_df['category'].fillna('') + ' ' +
            self.products_df['description'].fillna('')
        )
        
        # Create TF-IDF matrix
        tfidf_matrix = self.tfidf.fit_transform(self.products_df['combined_features'])
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        
    def recommend_similar_products(self, product_id, n_recommendations=5):
        """Find similar products based on content"""
        try:
            product_idx = self.products_df[self.products_df['id'] == product_id].index[0]
        except IndexError:
            return []
        
        # Get similarity scores
        similarity_scores = list(enumerate(self.similarity_matrix[product_idx]))
        similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        
        # Get top similar products (excluding the product itself)
        similar_indices = [i[0] for i in similarity_scores[1:n_recommendations+1]]
        
        return self.products_df.iloc[similar_indices]['id'].tolist()
```

### **C. Hybrid Recommendation System**
```python
# Combine collaborative and content-based approaches
class HybridRecommender:
    def __init__(self, collaborative_weight=0.7, content_weight=0.3):
        self.collaborative = CollaborativeRecommender()
        self.content_based = ContentBasedRecommender()
        self.collab_weight = collaborative_weight
        self.content_weight = content_weight
    
    def fit(self, orders_df, products_df):
        """Train both recommendation models"""
        # Train collaborative filtering
        user_item_matrix = self.collaborative.create_user_item_matrix(orders_df)
        self.collaborative.fit(user_item_matrix)
        
        # Train content-based filtering
        self.content_based.prepare_product_features(products_df)
    
    def get_hybrid_recommendations(self, customer_id, n_recommendations=10):
        """Get hybrid recommendations combining both approaches"""
        # Get collaborative recommendations
        collab_recs = self.collaborative.recommend_products(
            customer_id, n_recommendations * 2
        )
        
        # Get content-based recommendations based on customer's purchase history
        customer_purchases = self.get_customer_purchases(customer_id)
        content_recs = []
        
        for product_id in customer_purchases[-3:]:  # Use last 3 purchases
            similar_products = self.content_based.recommend_similar_products(
                product_id, n_recommendations
            )
            content_recs.extend(similar_products)
        
        # Combine recommendations with weights
        hybrid_scores = {}
        
        for product in collab_recs:
            hybrid_scores[product] = self.collab_weight
        
        for product in content_recs:
            if product in hybrid_scores:
                hybrid_scores[product] += self.content_weight
            else:
                hybrid_scores[product] = self.content_weight
        
        # Sort by score and return top recommendations
        sorted_recs = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return [product_id for product_id, score in sorted_recs[:n_recommendations]]
```

---

## 📊 **4. Inventory Optimization Models**

### **A. ABC Analysis with ML Enhancement**
```python
# Automated ABC classification with clustering
from sklearn.cluster import KMeans
import numpy as np

class MLEnhancedABCAnalysis:
    def __init__(self):
        self.kmeans = KMeans(n_clusters=3, random_state=42)
    
    def calculate_abc_features(self, products_df, orders_df):
        """Calculate features for ABC analysis"""
        # Calculate product metrics
        product_metrics = orders_df.groupby('product_id').agg({
            'quantity': 'sum',
            'total_amount': 'sum',
            'order_id': 'nunique',
            'order_date': ['min', 'max']
        }).round(2)
        
        product_metrics.columns = [
            'total_quantity', 'total_revenue', 'order_frequency',
            'first_order', 'last_order'
        ]
        
        # Calculate additional metrics
        product_metrics['revenue_per_unit'] = (
            product_metrics['total_revenue'] / product_metrics['total_quantity']
        )
        
        product_metrics['days_active'] = (
            product_metrics['last_order'] - product_metrics['first_order']
        ).dt.days
        
        product_metrics['velocity'] = (
            product_metrics['total_quantity'] / 
            np.maximum(product_metrics['days_active'], 1)
        )
        
        return product_metrics
    
    def classify_products(self, product_metrics):
        """Classify products using ML-enhanced ABC analysis"""
        # Normalize features for clustering
        features = ['total_revenue', 'total_quantity', 'velocity']
        X = product_metrics[features].values
        X_normalized = (X - X.mean(axis=0)) / X.std(axis=0)
        
        # Perform clustering
        clusters = self.kmeans.fit_predict(X_normalized)
        product_metrics['cluster'] = clusters
        
        # Map clusters to ABC categories based on revenue contribution
        cluster_revenue = product_metrics.groupby('cluster')['total_revenue'].sum()
        cluster_mapping = {
            cluster_revenue.idxmax(): 'A',  # Highest revenue cluster
            cluster_revenue.idxmin(): 'C',  # Lowest revenue cluster
        }
        
        # Middle cluster gets B
        remaining_cluster = set(range(3)) - set(cluster_mapping.keys())
        cluster_mapping[list(remaining_cluster)[0]] = 'B'
        
        product_metrics['abc_category'] = product_metrics['cluster'].map(cluster_mapping)
        
        return product_metrics
```

### **B. Dynamic Reorder Point Calculation**
```python
# ML-based reorder point optimization
class DynamicReorderOptimizer:
    def __init__(self):
        self.demand_model = None
        self.lead_time_model = None
    
    def calculate_safety_stock(self, product_id, service_level=0.95):
        """Calculate safety stock using demand and lead time variability"""
        # Get historical demand and lead time data
        demand_std = self.get_demand_std(product_id)
        lead_time_avg = self.get_avg_lead_time(product_id)
        lead_time_std = self.get_lead_time_std(product_id)
        
        # Z-score for service level
        from scipy.stats import norm
        z_score = norm.ppf(service_level)
        
        # Safety stock formula considering both demand and lead time variability
        safety_stock = z_score * np.sqrt(
            (lead_time_avg * demand_std**2) + 
            (self.get_avg_demand(product_id)**2 * lead_time_std**2)
        )
        
        return max(safety_stock, 0)
    
    def calculate_reorder_point(self, product_id, service_level=0.95):
        """Calculate optimal reorder point"""
        avg_demand = self.get_avg_demand(product_id)
        avg_lead_time = self.get_avg_lead_time(product_id)
        safety_stock = self.calculate_safety_stock(product_id, service_level)
        
        reorder_point = (avg_demand * avg_lead_time) + safety_stock
        
        return {
            'product_id': product_id,
            'reorder_point': reorder_point,
            'safety_stock': safety_stock,
            'avg_demand': avg_demand,
            'avg_lead_time': avg_lead_time,
            'service_level': service_level
        }
```

---

## 🚨 **5. Anomaly Detection Systems**

### **A. Order Fraud Detection**
```python
# Isolation Forest for fraud detection
from sklearn.ensemble import IsolationForest
import pandas as pd

class OrderFraudDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
    def engineer_fraud_features(self, orders_df):
        """Create features for fraud detection"""
        # Time-based features
        orders_df['hour'] = orders_df['order_date'].dt.hour
        orders_df['day_of_week'] = orders_df['order_date'].dt.dayofweek
        orders_df['is_weekend'] = orders_df['day_of_week'].isin([5, 6]).astype(int)
        
        # Order value features
        orders_df['order_value_zscore'] = (
            orders_df['total_amount'] - orders_df['total_amount'].mean()
        ) / orders_df['total_amount'].std()
        
        # Customer behavior features
        customer_stats = orders_df.groupby('customer_id').agg({
            'total_amount': ['mean', 'std', 'count'],
            'order_date': lambda x: (x.max() - x.min()).days
        })
        
        customer_stats.columns = [
            'customer_avg_order', 'customer_order_std', 
            'customer_order_count', 'customer_days_active'
        ]
        
        orders_with_features = orders_df.merge(
            customer_stats, left_on='customer_id', right_index=True
        )
        
        # Deviation from customer's normal behavior
        orders_with_features['value_deviation'] = abs(
            orders_with_features['total_amount'] - 
            orders_with_features['customer_avg_order']
        ) / orders_with_features['customer_order_std'].fillna(1)
        
        return orders_with_features
    
    def detect_fraud(self, orders_df):
        """Detect fraudulent orders"""
        features_df = self.engineer_fraud_features(orders_df)
        
        fraud_features = [
            'total_amount', 'hour', 'is_weekend', 'order_value_zscore',
            'customer_order_count', 'value_deviation'
        ]
        
        X = features_df[fraud_features].fillna(0)
        
        # Predict anomalies
        anomaly_scores = self.model.fit_predict(X)
        features_df['is_anomaly'] = (anomaly_scores == -1).astype(int)
        features_df['anomaly_score'] = self.model.decision_function(X)
        
        return features_df[features_df['is_anomaly'] == 1]
```

---

## 📈 **Implementation Roadmap**

### **Phase 1: Quick Wins (Month 1)**
```python
# High-impact, low-complexity models
priority_models = {
    "demand_forecasting": {
        "model": "Prophet",
        "complexity": "Low",
        "impact": "High",
        "timeline": "2 weeks"
    },
    "abc_analysis": {
        "model": "K-Means Clustering",
        "complexity": "Low", 
        "impact": "Medium",
        "timeline": "1 week"
    },
    "basic_recommendations": {
        "model": "Collaborative Filtering",
        "complexity": "Medium",
        "impact": "High",
        "timeline": "3 weeks"
    }
}
```

### **Phase 2: Advanced Analytics (Months 2-3)**
```python
# More sophisticated models
advanced_models = {
    "customer_segmentation": {
        "model": "RFM + ML Clustering",
        "complexity": "Medium",
        "impact": "High",
        "timeline": "3 weeks"
    },
    "churn_prediction": {
        "model": "Random Forest",
        "complexity": "Medium",
        "impact": "Medium",
        "timeline": "2 weeks"
    },
    "clv_prediction": {
        "model": "Lifetimes + ML",
        "complexity": "High",
        "impact": "High",
        "timeline": "4 weeks"
    }
}
```

This comprehensive ML strategy provides the foundation for building intelligent, data-driven features into your Orders & Inventory Management System! 🚀

Would you like me to elaborate on any specific model or start implementing the first phase?

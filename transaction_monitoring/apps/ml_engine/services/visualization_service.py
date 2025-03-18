"""
Visualization service for ML models and analytics.

This service provides functions for generating visualizations of ML model results,
with a focus on response code patterns and fraud detection.
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Dict, Any, List, Optional, Tuple
import io
import base64
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, Q
from apps.transactions.models import Transaction
from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES, RESPONSE_CODE_DESCRIPTIONS

logger = logging.getLogger(__name__)


def generate_response_code_distribution_plot(days: int = 30) -> Optional[str]:
    """
    Generate a plot showing the distribution of response codes.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Count response codes
        response_code_counts = transactions.values('response_code').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Convert to DataFrame
        df = pd.DataFrame(response_code_counts)
        
        # Skip if no data
        if df.empty:
            logger.warning("No response code data available for visualization")
            return None
        
        # Add descriptions
        df['description'] = df['response_code'].apply(
            lambda code: RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')
        )
        
        # Add risk level
        def get_risk_level(code):
            if code in HIGH_RISK_RESPONSE_CODES:
                return 'High'
            elif code in MEDIUM_RISK_RESPONSE_CODES:
                return 'Medium'
            elif code == '00':
                return 'Low'
            else:
                return 'Unknown'
        
        df['risk_level'] = df['response_code'].apply(get_risk_level)
        
        # Sort by count
        df = df.sort_values('count', ascending=False).head(15)  # Top 15 codes
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Create color map based on risk level
        colors = {
            'High': 'red',
            'Medium': 'orange',
            'Low': 'green',
            'Unknown': 'gray'
        }
        
        bar_colors = [colors[level] for level in df['risk_level']]
        
        # Create bar chart
        bars = plt.bar(
            df['response_code'] + ' - ' + df['description'], 
            df['count'],
            color=bar_colors
        )
        
        # Add count labels
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.1,
                f'{height:.0f}',
                ha='center', va='bottom',
                rotation=0
            )
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors['High'], label='High Risk'),
            Patch(facecolor=colors['Medium'], label='Medium Risk'),
            Patch(facecolor=colors['Low'], label='Low Risk'),
            Patch(facecolor=colors['Unknown'], label='Unknown Risk')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Customize plot
        plt.title(f'Response Code Distribution (Last {days} Days)')
        plt.xlabel('Response Code')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating response code distribution plot: {str(e)}", exc_info=True)
        return None


def generate_response_code_time_series(days: int = 30, interval: str = 'day') -> Optional[str]:
    """
    Generate a time series plot of response codes over time.
    
    Args:
        days: Number of days to look back
        interval: Time interval for grouping ('day', 'week', 'hour')
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(list(transactions.values('timestamp', 'response_code')))
        
        # Skip if no data
        if df.empty:
            logger.warning("No response code data available for time series visualization")
            return None
        
        # Add risk level
        def get_risk_category(code):
            if code in HIGH_RISK_RESPONSE_CODES:
                return 'High Risk'
            elif code in MEDIUM_RISK_RESPONSE_CODES:
                return 'Medium Risk'
            elif code == '00':
                return 'Approved'
            else:
                return 'Other'
        
        df['risk_category'] = df['response_code'].apply(get_risk_category)
        
        # Set timestamp as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group by time interval and risk category
        if interval == 'hour':
            df['time_group'] = df['timestamp'].dt.floor('H')
        elif interval == 'week':
            df['time_group'] = df['timestamp'].dt.floor('W')
        else:  # default to day
            df['time_group'] = df['timestamp'].dt.floor('D')
        
        # Count by time group and risk category
        time_series = df.groupby(['time_group', 'risk_category']).size().unstack(fill_value=0)
        
        # Create plot
        plt.figure(figsize=(14, 8))
        
        # Define colors
        colors = {
            'High Risk': 'red',
            'Medium Risk': 'orange',
            'Approved': 'green',
            'Other': 'gray'
        }
        
        # Plot each risk category
        for category in time_series.columns:
            if category in colors:
                plt.plot(
                    time_series.index, 
                    time_series[category], 
                    label=category,
                    color=colors[category],
                    marker='o',
                    linestyle='-',
                    linewidth=2,
                    markersize=5
                )
        
        # Customize plot
        plt.title(f'Response Code Trends (Last {days} Days)')
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Format x-axis dates
        if interval == 'hour':
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=4))
        elif interval == 'week':
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        else:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating response code time series: {str(e)}", exc_info=True)
        return None


def generate_response_code_heatmap(days: int = 30) -> Optional[str]:
    """
    Generate a heatmap showing the relationship between response codes and channels.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Count by response code and channel
        counts = transactions.values('response_code', 'channel').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Convert to DataFrame
        df = pd.DataFrame(counts)
        
        # Skip if no data
        if df.empty:
            logger.warning("No response code data available for heatmap visualization")
            return None
        
        # Pivot to create heatmap data
        pivot_df = df.pivot_table(
            index='response_code', 
            columns='channel', 
            values='count',
            fill_value=0
        )
        
        # Sort by total count
        pivot_df['total'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values('total', ascending=False).drop('total', axis=1)
        
        # Limit to top 15 response codes
        pivot_df = pivot_df.head(15)
        
        # Create plot
        plt.figure(figsize=(12, 10))
        
        # Create heatmap
        sns.heatmap(
            pivot_df, 
            annot=True, 
            fmt='g', 
            cmap='YlOrRd',
            linewidths=.5,
            cbar_kws={'label': 'Count'}
        )
        
        # Add response code descriptions
        labels = [f"{code} - {RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')}" for code in pivot_df.index]
        plt.yticks(np.arange(0.5, len(labels)), labels, rotation=0)
        
        # Customize plot
        plt.title(f'Response Code by Channel (Last {days} Days)')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating response code heatmap: {str(e)}", exc_info=True)
        return None


def generate_risk_score_by_response_code(days: int = 30) -> Optional[str]:
    """
    Generate a plot showing average risk scores by response code.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range with ML predictions
        from apps.ml_engine.models import MLPrediction
        
        # Get all transactions with predictions
        predictions = MLPrediction.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Get transaction IDs
        transaction_ids = predictions.values_list('transaction_id', flat=True).distinct()
        
        # Get transactions
        transactions = Transaction.objects.filter(transaction_id__in=transaction_ids)
        
        # Create a mapping of transaction_id to response_code
        tx_to_response = {tx.transaction_id: tx.response_code for tx in transactions}
        
        # Calculate average prediction by response code
        prediction_data = []
        for prediction in predictions:
            if prediction.transaction_id in tx_to_response:
                prediction_data.append({
                    'transaction_id': prediction.transaction_id,
                    'response_code': tx_to_response[prediction.transaction_id],
                    'prediction': prediction.prediction
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(prediction_data)
        
        # Skip if no data
        if df.empty:
            logger.warning("No prediction data available for risk score visualization")
            return None
        
        # Calculate average prediction by response code
        avg_by_code = df.groupby('response_code')['prediction'].mean().reset_index()
        
        # Add descriptions
        avg_by_code['description'] = avg_by_code['response_code'].apply(
            lambda code: RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')
        )
        
        # Add risk level
        def get_risk_level(code):
            if code in HIGH_RISK_RESPONSE_CODES:
                return 'High'
            elif code in MEDIUM_RISK_RESPONSE_CODES:
                return 'Medium'
            elif code == '00':
                return 'Low'
            else:
                return 'Unknown'
        
        avg_by_code['risk_level'] = avg_by_code['response_code'].apply(get_risk_level)
        
        # Sort by prediction
        avg_by_code = avg_by_code.sort_values('prediction', ascending=False)
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Create color map based on risk level
        colors = {
            'High': 'red',
            'Medium': 'orange',
            'Low': 'green',
            'Unknown': 'gray'
        }
        
        bar_colors = [colors[level] for level in avg_by_code['risk_level']]
        
        # Create bar chart
        bars = plt.bar(
            avg_by_code['response_code'] + ' - ' + avg_by_code['description'], 
            avg_by_code['prediction'],
            color=bar_colors
        )
        
        # Add score labels
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.1,
                f'{height:.1f}',
                ha='center', va='bottom',
                rotation=0
            )
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors['High'], label='High Risk'),
            Patch(facecolor=colors['Medium'], label='Medium Risk'),
            Patch(facecolor=colors['Low'], label='Low Risk'),
            Patch(facecolor=colors['Unknown'], label='Unknown Risk')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Customize plot
        plt.title(f'Average Risk Score by Response Code (Last {days} Days)')
        plt.xlabel('Response Code')
        plt.ylabel('Average Risk Score')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)  # Risk scores are 0-100
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating risk score by response code plot: {str(e)}", exc_info=True)
        return None


def generate_response_code_sequence_plot(user_id: str, days: int = 30) -> Optional[str]:
    """
    Generate a plot showing the sequence of response codes for a user.
    
    Args:
        user_id: User ID to analyze
        days: Number of days to look back
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions for the user in date range
        transactions = Transaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        # Convert to DataFrame
        df = pd.DataFrame(list(transactions.values('timestamp', 'response_code', 'channel', 'amount')))
        
        # Skip if no data
        if df.empty:
            logger.warning(f"No response code data available for user {user_id}")
            return None
        
        # Add risk level
        def get_risk_level(code):
            if code in HIGH_RISK_RESPONSE_CODES:
                return 'High'
            elif code in MEDIUM_RISK_RESPONSE_CODES:
                return 'Medium'
            elif code == '00':
                return 'Low'
            else:
                return 'Unknown'
        
        df['risk_level'] = df['response_code'].apply(get_risk_level)
        
        # Add description
        df['description'] = df['response_code'].apply(
            lambda code: RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')
        )
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Define colors
        colors = {
            'High': 'red',
            'Medium': 'orange',
            'Low': 'green',
            'Unknown': 'gray'
        }
        
        # Plot response codes
        for i, row in df.iterrows():
            ax1.scatter(
                row['timestamp'], 
                i, 
                color=colors[row['risk_level']], 
                s=100,
                label=row['risk_level'] if i == 0 else ""
            )
            ax1.text(
                row['timestamp'], 
                i + 0.1, 
                f"{row['response_code']} - {row['description']}",
                ha='center', 
                va='bottom',
                rotation=0,
                fontsize=8
            )
        
        # Plot amounts
        ax2.bar(
            df['timestamp'],
            df['amount'],
            color=df['risk_level'].map(colors),
            alpha=0.7
        )
        
        # Customize plots
        ax1.set_title(f'Response Code Sequence for User {user_id} (Last {days} Days)')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Transaction Sequence')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Remove y-ticks
        ax1.set_yticks([])
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors['High'], label='High Risk'),
            Patch(facecolor=colors['Medium'], label='Medium Risk'),
            Patch(facecolor=colors['Low'], label='Low Risk'),
            Patch(facecolor=colors['Unknown'], label='Unknown Risk')
        ]
        ax1.legend(handles=legend_elements, loc='upper right')
        
        # Customize amount plot
        ax2.set_title('Transaction Amounts')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Amount')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Format x-axis dates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating response code sequence plot: {str(e)}", exc_info=True)
        return None


def generate_response_code_sankey(days: int = 30) -> Optional[str]:
    """
    Generate a Sankey diagram showing the flow from channels to response codes to risk levels.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Check if plotly is available
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        logger.warning("Plotly not available. Install with 'pip install plotly' for Sankey diagrams.")
        return None
    
    try:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(list(transactions.values('channel', 'response_code')))
        
        # Skip if no data
        if df.empty:
            logger.warning("No response code data available for Sankey diagram")
            return None
        
        # Add risk level
        def get_risk_level(code):
            if code in HIGH_RISK_RESPONSE_CODES:
                return 'High Risk'
            elif code in MEDIUM_RISK_RESPONSE_CODES:
                return 'Medium Risk'
            elif code == '00':
                return 'Approved'
            else:
                return 'Other'
        
        df['risk_level'] = df['response_code'].apply(get_risk_level)
        
        # Add description
        df['description'] = df['response_code'].apply(
            lambda code: RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')
        )
        
        # Create node lists
        channels = df['channel'].unique().tolist()
        response_codes = df['response_code'].unique().tolist()
        risk_levels = df['risk_level'].unique().tolist()
        
        # Create node labels
        channel_labels = channels
        response_code_labels = [f"{code} - {RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')}" for code in response_codes]
        risk_level_labels = risk_levels
        
        # Create node list
        nodes = channel_labels + response_code_labels + risk_level_labels
        
        # Create source-target pairs and values
        sources = []
        targets = []
        values = []
        
        # Channel to response code
        for channel in channels:
            for code in response_codes:
                count = df[(df['channel'] == channel) & (df['response_code'] == code)].shape[0]
                if count > 0:
                    sources.append(nodes.index(channel))
                    targets.append(nodes.index(f"{code} - {RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')}"))
                    values.append(count)
        
        # Response code to risk level
        for code in response_codes:
            for level in risk_levels:
                count = df[(df['response_code'] == code) & (df['risk_level'] == level)].shape[0]
                if count > 0:
                    sources.append(nodes.index(f"{code} - {RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')}"))
                    targets.append(nodes.index(level))
                    values.append(count)
        
        # Create color map
        color_map = {
            'High Risk': 'rgba(255, 0, 0, 0.8)',
            'Medium Risk': 'rgba(255, 165, 0, 0.8)',
            'Approved': 'rgba(0, 128, 0, 0.8)',
            'Other': 'rgba(128, 128, 128, 0.8)',
            'pos': 'rgba(0, 0, 255, 0.8)',
            'ecommerce': 'rgba(75, 0, 130, 0.8)',
            'wallet': 'rgba(0, 128, 128, 0.8)'
        }
        
        # Create node colors
        node_colors = []
        for node in nodes:
            if node in channels:
                node_colors.append(color_map.get(node, 'rgba(128, 128, 128, 0.8)'))
            elif node in risk_levels:
                node_colors.append(color_map.get(node, 'rgba(128, 128, 128, 0.8)'))
            else:
                # For response codes, use risk level color
                code = node.split(' - ')[0]
                level = get_risk_level(code)
                node_colors.append(color_map.get(level, 'rgba(128, 128, 128, 0.8)'))
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=nodes,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        )])
        
        # Customize layout
        fig.update_layout(
            title_text=f"Response Code Flow (Last {days} Days)",
            font_size=10,
            height=800,
            width=1000
        )
        
        # Save as PNG
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating response code Sankey diagram: {str(e)}", exc_info=True)
        return None


def generate_shap_summary_plot(model, features: Dict[str, Any]) -> Optional[str]:
    """
    Generate a SHAP summary plot for a model prediction.
    
    Args:
        model: The ML model
        features: Dictionary of features
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Check if SHAP is available
        import shap
    except ImportError:
        logger.warning("SHAP not available. Install with 'pip install shap' for SHAP plots.")
        return None
    
    try:
        # Convert features to DataFrame
        features_df = pd.DataFrame([features])
        
        # For pipeline models, we need to get the classifier
        if hasattr(model, 'named_steps') and 'classifier' in model.named_steps:
            classifier = model.named_steps['classifier']
            
            # Apply preprocessing
            if 'preprocessor' in model.named_steps:
                preprocessor = model.named_steps['preprocessor']
                X_processed = preprocessor.transform(features_df)
                
                # For tree-based models
                if hasattr(classifier, 'feature_importances_'):
                    # Create explainer
                    explainer = shap.TreeExplainer(classifier)
                    
                    # Calculate SHAP values
                    shap_values = explainer.shap_values(X_processed)
                    
                    # For binary classification, shap_values is a list with two elements
                    if isinstance(shap_values, list) and len(shap_values) == 2:
                        shap_values = shap_values[1]  # Use values for class 1 (fraud)
                    
                    # Get feature names after preprocessing
                    if hasattr(preprocessor, 'get_feature_names_out'):
                        feature_names = preprocessor.get_feature_names_out()
                    else:
                        # Fallback to generic names
                        feature_names = [f'feature_{i}' for i in range(X_processed.shape[1])]
                    
                    # Create plot
                    plt.figure(figsize=(10, 8))
                    
                    # Create summary plot
                    shap.summary_plot(
                        shap_values, 
                        X_processed,
                        feature_names=feature_names,
                        show=False
                    )
                    
                    # Save plot to a bytes buffer
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    plt.close()
                    
                    # Encode the image to base64
                    buf.seek(0)
                    img_str = base64.b64encode(buf.read()).decode('utf-8')
                    
                    return img_str
        
        # For simple models (not pipelines)
        elif hasattr(model, 'feature_importances_'):
            # Create explainer
            explainer = shap.TreeExplainer(model)
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(features_df)
            
            # For binary classification, shap_values is a list with two elements
            if isinstance(shap_values, list) and len(shap_values) == 2:
                shap_values = shap_values[1]  # Use values for class 1 (fraud)
            
            # Create plot
            plt.figure(figsize=(10, 8))
            
            # Create summary plot
            shap.summary_plot(
                shap_values, 
                features_df,
                show=False
            )
            
            # Save plot to a bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode the image to base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return img_str
        
        return None
    
    except Exception as e:
        logger.error(f"Error generating SHAP summary plot: {str(e)}", exc_info=True)
        return None
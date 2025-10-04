"""
Module de graphiques réutilisables pour le dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size

# ============================================================================
# PIE CHART - RÉPARTITION EXTENSIONS
# ============================================================================

def create_extensions_pie_chart(df: pd.DataFrame, title: str = "Répartition par Extension") -> go.Figure:
    """
    Crée un pie chart pour la répartition des extensions.
    
    Args:
        df: DataFrame avec colonnes extension, file_count, total_size
        title: Titre du graphique
        
    Returns:
        Figure Plotly
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
    
    # Garder top 10 + regrouper le reste dans "Autres"
    if len(df) > 10:
        top_10 = df.head(10).copy()
        others = pd.DataFrame({
            'extension': ['Autres'],
            'file_count': [df.iloc[10:]['file_count'].sum()],
            'total_size': [df.iloc[10:]['total_size'].sum()]
        })
        df_plot = pd.concat([top_10, others], ignore_index=True)
    else:
        df_plot = df.copy()
    
    # Formater les tailles
    df_plot['total_size_formatted'] = df_plot['total_size'].apply(format_size)
    
    fig = go.Figure(data=[go.Pie(
        labels=df_plot['extension'],
        values=df_plot['total_size'],
        hole=0.3,
        hovertemplate='<b>%{label}</b><br>Volume: %{customdata[0]}<br>Fichiers: %{customdata[1]:,}<br>Part: %{percent}<extra></extra>',
        customdata=df_plot[['total_size_formatted', 'file_count']].values,
        textposition='auto',
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=500,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    return fig

# ============================================================================
# TREEMAP - VOLUMES HIÉRARCHIQUES
# ============================================================================

@st.cache_data(ttl=300)
def get_directory_hierarchy(_db, scan_id: str, max_depth: int = 3):
    """
    Récupère hiérarchie de dossiers pour treemap.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        max_depth: Profondeur maximale
        
    Returns:
        DataFrame avec colonnes: path, parent, size, file_count
    """
    cursor = _db.conn.cursor()
    
    # Récupérer stats par dossier
    cursor.execute("""
        SELECT 
            parent_dir as path,
            SUM(size_bytes) as total_size,
            COUNT(*) as file_count
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY parent_dir
        ORDER BY total_size DESC
        LIMIT 100
    """, (scan_id,))
    
    data = []
    for path, size, count in cursor.fetchall():
        if not path:
            continue
        
        # Calculer profondeur
        depth = path.count('/')
        if depth > max_depth:
            continue
        
        # Déterminer parent
        parent = str(Path(path).parent) if path != '/' else ''
        
        data.append({
            'path': path,
            'parent': parent,
            'size': size,
            'file_count': count
        })
    
    return pd.DataFrame(data)

def create_treemap(df: pd.DataFrame, title: str = "Volumes Hiérarchiques") -> go.Figure:
    """
    Crée un treemap hiérarchique.
    
    Args:
        df: DataFrame avec colonnes path, parent, size, file_count
        title: Titre du graphique
        
    Returns:
        Figure Plotly
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
    
    # Formater les tailles
    df['size_formatted'] = df['size'].apply(format_size)
    
    fig = go.Figure(go.Treemap(
        labels=df['path'],
        parents=df['parent'],
        values=df['size'],
        text=df['size_formatted'],
        hovertemplate='<b>%{label}</b><br>Volume: %{text}<br>Fichiers: %{customdata:,}<extra></extra>',
        customdata=df['file_count'],
        textposition='middle center',
        marker=dict(
            colorscale='Viridis',
            cmid=df['size'].median()
        )
    ))
    
    fig.update_layout(
        title=title,
        height=600
    )
    
    return fig

# ============================================================================
# TIMELINE - DISTRIBUTION TEMPORELLE
# ============================================================================

@st.cache_data(ttl=300)
def get_temporal_data(_db, scan_id: str, groupby: str = 'month'):
    """
    Récupère distribution temporelle des fichiers.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        groupby: 'day', 'month', ou 'year'
        
    Returns:
        DataFrame avec colonnes: period, count, total_size
    """
    cursor = _db.conn.cursor()
    
    # Format de date selon groupby
    date_format = {
        'day': '%Y-%m-%d',
        'month': '%Y-%m',
        'year': '%Y'
    }.get(groupby, '%Y-%m')
    
    cursor.execute(f"""
        SELECT 
            strftime('{date_format}', mtime, 'unixepoch') as period,
            COUNT(*) as count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0 AND mtime IS NOT NULL
        GROUP BY period
        ORDER BY period
    """, (scan_id,))
    
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=['period', 'count', 'total_size'])

def create_timeline_chart(df: pd.DataFrame, title: str = "Distribution Temporelle") -> go.Figure:
    """
    Crée un graphique timeline avec double axe Y.
    
    Args:
        df: DataFrame avec colonnes period, count, total_size
        title: Titre du graphique
        
    Returns:
        Figure Plotly
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", showarrow=False)
        return fig
    
    # Formater les tailles
    df['total_size_formatted'] = df['total_size'].apply(format_size)
    
    # Créer figure avec double axe Y
    fig = go.Figure()
    
    # Trace 1: Nombre de fichiers (barres)
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['count'],
        name='Nombre de fichiers',
        marker_color='steelblue',
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Fichiers: %{y:,}<extra></extra>'
    ))
    
    # Trace 2: Volume total (ligne)
    fig.add_trace(go.Scatter(
        x=df['period'],
        y=df['total_size'],
        name='Volume total',
        mode='lines+markers',
        marker_color='coral',
        line=dict(width=2),
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>Volume: %{customdata}<extra></extra>',
        customdata=df['total_size_formatted']
    ))
    
    # Layout avec double axe
    fig.update_layout(
        title=title,
        xaxis=dict(title='Période'),
        yaxis=dict(
            title='Nombre de fichiers',
            side='left'
        ),
        yaxis2=dict(
            title='Volume total (bytes)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

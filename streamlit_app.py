import os
import re
import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# ---- Env (Modal secret must define these) ----
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# ---- Data access ----
@st.cache_data(ttl=3600)  # cache for 1 hour
def get_menu_data():
    """Fetch menu data from Supabase -> DataFrame (safe)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        return pd.DataFrame()
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        res = sb.table("chickfila_menu").select("*").execute()
        rows = res.data or []
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()

def clean_calories(calories_str):
    """Extract numeric calories from string like '300 Cal' -> 300."""
    if pd.isna(calories_str):
        return None
    try:
        nums = re.findall(r"\d+", str(calories_str))
        return int(nums[0]) if nums else None
    except Exception:
        return None

# ---- App ----
def main():
    st.set_page_config(page_title="Chick-fil-A Menu Analysis", layout="wide")
    st.title("Chick-fil-A Side Menu Dashboard")

    df = get_menu_data()

    # Debug breadcrumb so you can see if data arrived
    st.caption(f"Rows fetched: {len(df)} | Columns: {list(df.columns)}")

    if df.empty:
        st.warning("No menu data available. Please run the data pipeline first or check Supabase policies.")
        return

    # Safe conversions / derived columns
    if "extracted_at" in df.columns:
        df["extracted_at"] = pd.to_datetime(df["extracted_at"], errors="coerce")
    if "calories" in df.columns:
        df["calories_numeric"] = df["calories"].apply(clean_calories)
    else:
        df["calories_numeric"] = pd.NA

    # ---- Sidebar filters ----
    st.sidebar.header("Filters")

    # Category filter: handle missing 'category'
    categories = ["All"]
    if "category" in df.columns:
        categories += sorted([c for c in df["category"].dropna().unique().tolist() if str(c).strip() != ""])
    selected_category = st.sidebar.selectbox("Category", categories, index=0)

    show_vegetarian = st.sidebar.checkbox("Vegetarian Only")
    show_gluten_free = st.sidebar.checkbox("Gluten-Free Only")

    # Apply filters safely
    filtered_df = df.copy()
    if selected_category != "All" and "category" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
    if show_vegetarian and "is_vegetarian" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_vegetarian"] == True]
    if show_gluten_free and "is_gluten_free" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_gluten_free"] == True]

    # ---- KPI row ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Menu Items", len(df))
    with col2:
        st.metric("Categories", df["category"].nunique() if "category" in df else 0)
    with col3:
        veg_count = int(df["is_vegetarian"].sum()) if "is_vegetarian" in df else 0
        st.metric("Vegetarian Options", veg_count)
    with col4:
        gf_count = int(df["is_gluten_free"].sum()) if "is_gluten_free" in df else 0
        st.metric("Gluten-Free Options", gf_count)

    # ---- Table ----
    st.subheader("Menu Items")
    display_columns = ["name", "category", "price", "calories", "is_vegetarian", "is_gluten_free"]
    available = [c for c in display_columns if c in filtered_df.columns]
    table_df = filtered_df[available].copy() if available else pd.DataFrame()
    if "category" in table_df.columns:
        table_df = table_df.sort_values("category", kind="stable")
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # ---- Visualizations ----
    st.subheader("Menu Analysis")
    colA, colB = st.columns(2)

    with colA:
        # Items by category
        if "category" in filtered_df.columns:
            counts = filtered_df["category"].value_counts()
            if not counts.empty:
                fig1 = px.pie(values=counts.values, names=counts.index, title="Menu Items by Category")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No category data available for chart.")
        else:
            st.info("Column 'category' not found — cannot plot category pie.")

    with colB:
        # Calories distribution
        cal = filtered_df["calories_numeric"].dropna() if "calories_numeric" in filtered_df.columns else pd.Series([], dtype="float")
        if not cal.empty:
            fig2 = px.histogram(filtered_df.dropna(subset=["calories_numeric"]),
                                x="calories_numeric",
                                title="Calories Distribution",
                                labels={"calories_numeric": "Calories"})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No numeric calories available to plot.")

    # ---- Allergen analysis ----
    st.subheader("Allergen Information")
    if "allergens" in filtered_df.columns:
        all_allergens = []
        for a in filtered_df["allergens"].dropna():
            if isinstance(a, list):
                all_allergens.extend(a)
            else:
                # if stored as comma-separated string
                s = str(a).strip()
                if s.startswith("[") and s.endswith("]"):
                    # looks like JSON array string
                    try:
                        import json
                        all_allergens.extend(json.loads(s))
                    except Exception:
                        pass
                elif s:
                    all_allergens.extend([t.strip() for t in s.split(",") if t.strip()])
        if all_allergens:
            counts = pd.Series(all_allergens).value_counts()
            fig3 = px.bar(x=counts.index, y=counts.values, title="Common Allergens in Menu",
                          labels={"x": "Allergen", "y": "Number of Items"})
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No allergen data to display.")
    else:
        st.info("Column 'allergens' not found — skipping allergen chart.")

    # ---- Item details ----
    st.subheader("Item Details")
    name_options = filtered_df["name"].dropna().unique().tolist() if "name" in filtered_df.columns else []
    if name_options:
        selected_item = st.selectbox("Select an item for details", name_options)
        item = filtered_df[filtered_df["name"] == selected_item].head(1)
        if not item.empty:
            row = item.iloc[0].to_dict()
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Category:** {row.get('category', 'N/A')}")
                st.write(f"**Price:** {row.get('price', 'N/A')}")
                st.write(f"**Calories:** {row.get('calories', 'N/A')}")
                allergens = row.get("allergens")
                if isinstance(allergens, list) and allergens:
                    st.write("**Allergens:**")
                    for a in allergens:
                        st.write(f"• {a}")
            with c2:
                st.write("**Description:**")
                st.write(row.get("description", "No description available"))
                tags = []
                if row.get("is_vegetarian"):
                    tags.append("Vegetarian")
                if row.get("is_gluten_free"):
                    tags.append("Gluten-Free")
                if tags:
                    st.write("**Dietary:**")
                    for t in tags:
                        st.write(t)
    else:
        st.info("No 'name' column or no items to display.")

if __name__ == "__main__":
    main()

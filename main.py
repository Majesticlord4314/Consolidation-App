import streamlit as st
import pandas as pd
import numpy as np
import io
import warnings

warnings.filterwarnings('ignore')

# Configure the Streamlit app
st.set_page_config(page_title="Inventory Consolidation Analysis", layout="wide")
st.title("Inventory Consolidation Analysis")
st.markdown("""
This app performs inventory rebalancing analysis using sales and stock data to generate movement recommendations between stores and warehouses.
Upload your CSV files below to get started.
""")

# File upload widgets
sales_file  = st.file_uploader("Upload Sales CSV", type=["csv"])
soh_file    = st.file_uploader("Upload Stock (SOH) CSV", type=["csv"])
format_file = st.file_uploader("Upload Format Template CSV", type=["csv"])

try:
    if sales_file and soh_file and format_file:
        # ─── Step 0: Load files ───────────────────────────────────────
        with st.spinner("Loading datasets..."):
            df_sales  = pd.read_csv(sales_file)
            df_soh    = pd.read_csv(soh_file)
            df_format = pd.read_csv(format_file)

            # Standardize column names
            df_sales.columns  = df_sales.columns.str.strip()
            df_soh.columns    = df_soh.columns.str.strip()
            df_format.columns = df_format.columns.str.strip()

            # Standardize ProductName to uppercase
            df_sales['ProductName'] = (
                df_sales['ProductName'].astype(str)
                         .str.strip()
                         .str.upper()
            )
            df_soh['ProductName'] = (
                df_soh['ProductName'].astype(str)
                       .str.strip()
                       .str.upper()
            )

            # Validate required columns
            for col in ['StoreName','ProductCode','ProductName','Quantity']:
                if col not in df_sales.columns:
                    st.error(f"Missing in Sales CSV: {col}")
                    st.stop()
            for col in ['StoreName','ProductCode','ProductName','ActualStock']:
                if col not in df_soh.columns:
                    st.error(f"Missing in SOH CSV: {col}")
                    st.stop()
            if 'Part No' not in df_format.columns:
                st.error("Missing in Format Template CSV: Part No")
                st.stop()

            # Filter to products in format template
            parts = (
                df_format['Part No']
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
            )
            valid_parts = {p for p in parts if p.lower() != 'nan'}
            if valid_parts:
                df_sales = df_sales[
                    df_sales['ProductCode']
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .isin(valid_parts)
                ]
                df_soh = df_soh[
                    df_soh['ProductCode']
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .isin(valid_parts)
                ]
            else:
                st.warning("No valid Part No values—skipping filter.")

        # ─── Step 1: Confirmation & Preview ─────────────────────────────
        st.success(f"Sales data loaded: {df_sales.shape}")
        st.success(f"SOH data loaded:   {df_soh.shape}")
        st.success(f"Format template:   {df_format.shape}")
        with st.expander("Show sample data"):
            st.markdown('<span style="color: orange; font-size: 0.95em;">Sales Columns:</span>', unsafe_allow_html=True)
            st.code(", ".join(df_sales.columns), language=None)
            st.dataframe(df_sales.head(5), use_container_width=True, height=min(220, 35+25*len(df_sales.head(5))))
            st.markdown('<span style="color: orange; font-size: 0.95em;">SOH Columns:</span>', unsafe_allow_html=True)
            st.code(", ".join(df_soh.columns), language=None)
            st.dataframe(df_soh.head(5), use_container_width=True, height=min(220, 35+25*len(df_soh.head(5))))
            st.markdown('<span style="color: orange; font-size: 0.95em;">Format Template Columns:</span>', unsafe_allow_html=True)
            st.code(", ".join(df_format.columns), language=None)
            st.dataframe(df_format.head(5), use_container_width=True, height=min(220, 35+25*len(df_format.head(5))))

        # ─── Step 2: Data Cleaning & Preparation ──────────────────────────
        st.header("Step 1: Data Cleaning & Preparation")
        
        # Extract unique brands for filtering
        brands_sales = df_sales['BrandName'].dropna().unique() if 'BrandName' in df_sales.columns else []
        brands_soh = df_soh['Brand'].dropna().unique() if 'Brand' in df_soh.columns else []
        all_brands = sorted(set(list(brands_sales) + list(brands_soh)))
        
        if all_brands:
            st.subheader("Brand Selection")
            st.write("Select which brands to include in the analysis:")
            
            # Add Check All option
            col1, col2 = st.columns([1, 4])
            with col1:
                check_all = st.checkbox("Check All", value=False, key="check_all")
            with col2:
                if st.button("Clear All", key="clear_all"):
                    for brand in all_brands:
                        st.session_state[f"brand_{brand}"] = False
                    st.rerun()
            
            # Create columns for checkboxes
            num_cols = min(4, len(all_brands))
            cols = st.columns(num_cols)
            
            selected_brands = []
            for i, brand in enumerate(all_brands):
                col_idx = i % num_cols
                with cols[col_idx]:
                    # Set default value based on check_all state
                    default_value = check_all if f"brand_{brand}" not in st.session_state else st.session_state[f"brand_{brand}"]
                    if check_all and f"brand_{brand}" not in st.session_state:
                        st.session_state[f"brand_{brand}"] = True
                    
                    if st.checkbox(brand, value=default_value, key=f"brand_{brand}"):
                        selected_brands.append(brand)
        
        # Store Brand Selection
        st.subheader("Store Brand Selection")
        st.write("Select which store brands to include in the analysis:")
        
        store_brands = ["Bose", "Imagine", "Icare"]
        
        # Add Check All option for stores
        col1, col2 = st.columns([1, 4])
        with col1:
            check_all_stores = st.checkbox("Check All Stores", value=False, key="check_all_stores")
        with col2:
            if st.button("Clear All Stores", key="clear_all_stores"):
                for store_brand in store_brands:
                    st.session_state[f"store_{store_brand}"] = False
                st.rerun()
        
        # Create columns for store checkboxes
        store_cols = st.columns(3)
        selected_store_brands = []
        for i, store_brand in enumerate(store_brands):
            with store_cols[i]:
                # Set default value based on check_all_stores state
                default_value = check_all_stores if f"store_{store_brand}" not in st.session_state else st.session_state[f"store_{store_brand}"]
                if check_all_stores and f"store_{store_brand}" not in st.session_state:
                    st.session_state[f"store_{store_brand}"] = True
                
                if st.checkbox(store_brand, value=default_value, key=f"store_{store_brand}"):
                    selected_store_brands.append(store_brand)
            
            # Filter data based on selected brands
            before = len(df_sales)
            if selected_brands:
                if 'BrandName' in df_sales.columns:
                    df_sales = df_sales[df_sales['BrandName'].isin(selected_brands)]
                if 'Brand' in df_soh.columns:
                    df_soh = df_soh[df_soh['Brand'].isin(selected_brands)]
                
                st.write(f"Included {len(selected_brands)} brands. Kept {len(df_sales)} rows from {before} total sales rows.")
                st.write(f"Selected brands: {', '.join(selected_brands)}")
            else:
                st.warning("No brands selected. Including all data.")
        else:
            st.info("No brand information found in the data. Proceeding with all products.")
        
        # Filter data based on selected store brands
        if selected_store_brands:
            before_sales = len(df_sales)
            before_soh = len(df_soh)
            
            # Create filter conditions for store names
            def store_filter(store_name, selected_stores):
                if pd.isna(store_name):
                    return False
                store_str = str(store_name).lower()
                for store_brand in selected_stores:
                    if store_brand.lower() in store_str:
                        return True
                return False
            
            # Apply store filtering
            df_sales = df_sales[df_sales['StoreName'].apply(lambda x: store_filter(x, selected_store_brands))]
            df_soh = df_soh[df_soh['StoreName'].apply(lambda x: store_filter(x, selected_store_brands))]
            
            st.write(f"Store filtering: Kept {len(df_sales)} sales rows (from {before_sales}) and {len(df_soh)} SOH rows (from {before_soh})")
            st.write(f"Selected store brands: {', '.join(selected_store_brands)}")
        else:
            st.warning("No store brands selected. Including all stores.")
            
        # Final data check
        if len(df_sales) == 0 or len(df_soh) == 0:
            st.error("No data remaining after filtering. Please adjust your brand/store selections.")
            st.stop()

        # ─── Step 3: Aggregation ───────────────────────────────────────
        st.header("Step 2: Aggregation")
        sales_agg = (
            df_sales
              .groupby(['StoreName','ProductCode'], as_index=False)
              .agg({'Quantity':'sum'})
              .rename(columns={
                  'StoreName':'Store',
                  'ProductCode':'Part No',
                  'Quantity':'Sales'
              })
        )
        soh_agg = (
            df_soh
              .groupby(['StoreName','ProductCode'], as_index=False)
              .agg({'ActualStock':'sum'})
              .rename(columns={
                  'StoreName':'Store',
                  'ProductCode':'Part No',
                  'ActualStock':'Stock'
              })
        )
        sales_agg['Sales'] = pd.to_numeric(sales_agg['Sales'], errors='coerce').fillna(0)
        soh_agg['Stock']   = pd.to_numeric(soh_agg['Stock'],   errors='coerce').fillna(0)

        prod_lookup = pd.concat([
            df_sales[['ProductCode','ProductName']],
            df_soh[['ProductCode','ProductName']]
        ]).drop_duplicates('ProductCode')

        agg_summary = pd.DataFrame({
            'Metric': [
                'Sales rows', 'SOH rows',
                'Unique stores in Sales', 'Unique stores in SOH',
                'Unique products in Sales', 'Unique products in SOH',
                'Total Sales qty', 'Total SOH qty'
            ],
            'Value': [
                sales_agg.shape[0], soh_agg.shape[0],
                sales_agg['Store'].nunique(), soh_agg['Store'].nunique(),
                sales_agg['Part No'].nunique(), soh_agg['Part No'].nunique(),
                sales_agg['Sales'].sum(), soh_agg['Stock'].sum()
            ]
        })
        st.table(agg_summary)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<b>Sales Aggregation Stats</b>", unsafe_allow_html=True)
            st.table(sales_agg[['Sales']].agg(['sum','mean','min','max']).round(2))
        with col2:
            st.markdown("<b>SOH Aggregation Stats</b>", unsafe_allow_html=True)
            st.table(soh_agg[['Stock']].agg(['sum','mean','min','max']).round(2))

        # ─── Step 4: Merge & Forecast ──────────────────────────────────
        st.header("Step 3: Merge & Forecast")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean", f"{sales_agg['Sales'].mean():.2f}")
        c2.metric("Min",  f"{sales_agg['Sales'].min():.2f}")
        c3.metric("Max",  f"{sales_agg['Sales'].max():.2f}")
        c4.metric("Std",  f"{sales_agg['Sales'].std():.2f}")
        df_merged = (
            pd.merge(sales_agg, soh_agg, on=['Store','Part No'], how='outer')
              .fillna({'Sales':0,'Stock':0})
        )
        df_merged = pd.merge(
            df_merged, prod_lookup,
            left_on='Part No', right_on='ProductCode', how='left'
        )
        df_merged.drop('ProductCode', axis=1, inplace=True)
        df_merged.rename(columns={'ProductName':'Product'}, inplace=True)
        df_merged['Forecast_Demand'] = df_merged['Sales']
        st.dataframe(df_merged.head())

        # ─── Step 5: Allocation Logic ──────────────────────────────────
        st.header("Step 4: Suggested Transfers")
        stock_lu = {(r.Store,r['Part No']):r.Stock for _,r in df_merged.iterrows()}
        sales_lu = {(r.Store,r['Part No']):r.Sales for _,r in df_merged.iterrows()}
        prod_map = {r['Part No']:r.Product for _,r in df_merged.iterrows()}

        warehouse_by_prod = {}
        stores_by_prod    = {}
        for (store, part), stk in stock_lu.items():
            if 'warehouse' in store.lower():
                warehouse_by_prod.setdefault(part,[]).append(store)
            if stk>0:
                stores_by_prod.setdefault(part,[]).append(store)

        available = stock_lu.copy()
        movements  = []
        processed  = set()
        pairs = df_merged[['Store','Part No','Forecast_Demand','Stock']].drop_duplicates()
        pairs = pairs[pairs['Forecast_Demand'] > pairs['Stock']]
        total = len(pairs)
        prog  = st.progress(0)

        for i, (dest, part, fc, stk) in enumerate(pairs.itertuples(index=False)):
            if (dest, part) in processed:
                continue
            processed.add((dest, part))
            rem = fc - stk

            # Warehouses first
            for src in warehouse_by_prod.get(part, []):
                if src == dest or rem <= 0:
                    continue
                avail = available[(src, part)]
                qty   = min(avail, rem)
                if qty > 0:
                    movements.append(dict(
                        ProductName=prod_map[part],
                        Product=part,
                        Source=src,
                        Destination=dest,
                        Quantity=qty
                    ))
                    available[(src, part)] -= qty
                    rem -= qty

            # Retail fallback
            if rem > 0:
                candidates = [
                    s for s in stores_by_prod.get(part, [])
                    if s != dest and 'warehouse' not in s.lower()
                ]
                candidates.sort(key=lambda s: sales_lu.get((s, part),0))
                for src in candidates:
                    if rem <= 0:
                        break
                    avail = available[(src, part)]
                    qty   = min(avail, rem)
                    if qty>0:
                        movements.append(dict(
                            ProductName=prod_map[part],
                            Product=part,
                            Source=src,
                            Destination=dest,
                            Quantity=qty
                        ))
                        available[(src, part)] -= qty
                        rem -= qty

            prog.progress((i+1)/total)
        prog.empty()

        # ─── Compile & Display Results ─────────────────────────────────
        result = pd.DataFrame(movements)
        if not result.empty:
            # Enrich with metrics
            result['From SOH']   = result.apply(lambda r: stock_lu[(r.Source, r.Product)], axis=1)
            result['To SOH']     = result.apply(lambda r: stock_lu[(r.Destination, r.Product)], axis=1)
            result['From Sales'] = result.apply(lambda r: sales_lu[(r.Source, r.Product)], axis=1)
            result['To Sales']   = result.apply(lambda r: sales_lu[(r.Destination, r.Product)], axis=1)

        st.header("Movement Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Movements", len(result))
        c2.metric("Total Qty to Transfer", int(result['Quantity'].sum()) if not result.empty else 0)
        c3.metric("Unique Products", result['Product'].nunique() if not result.empty else 0)

        st.subheader("Detailed Movements Preview")
        st.dataframe(result.head(50))

        st.subheader("Download Consolidation Report")
        def to_excel(df):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Consolidation_Report')
                wb  = writer.book
                ws  = writer.sheets['Consolidation_Report']
                fmt = wb.add_format({'bold':True,'text_wrap':True,'valign':'top','fg_color':'#D7E4BC','border':1})
                for i, col in enumerate(df.columns):
                    ws.write(0, i, col, fmt)
                    ws.set_column(i, i, 20)
            buf.seek(0)
            return buf

        excel_data = to_excel(result)
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name="consolidation_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- Analysis Summary and Detailed Movements ---
        with st.expander("Analysis Summary", expanded=False):
            st.write(f"**Total movements:** {len(result)}")
            st.write(f"**Sum of quantity to transfer:** {int(result['Quantity'].sum()) if not result.empty else 0}")
            st.write(f"**Unique products:** {result['Product'].nunique() if not result.empty else 0}")
            st.write(f"**Unique sources:** {result['Source'].nunique() if not result.empty else 0}")
            st.write(f"**Unique destinations:** {result['Destination'].nunique() if not result.empty else 0}")
        with st.expander("Full Detailed Movements Table", expanded=False):
            st.dataframe(result, use_container_width=True)


    else:
        st.warning("Please upload all three required CSV files.")
except Exception as e:
    st.error(f"Error: {e}")
    import traceback; st.code(traceback.format_exc())

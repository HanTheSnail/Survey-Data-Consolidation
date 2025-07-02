import streamlit as st
import pandas as pd
import io
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Survey Data Consolidation Tool",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Survey Data Consolidation Tool")
    st.markdown("**Consolidate bad response data with user information for panel provider reporting**")
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚫 Bad Responses Sheet")
        st.markdown("Upload the sheet containing User REF (Column A) of unusable responses")
        bad_responses_file = st.file_uploader(
            "Choose bad responses CSV file",
            type=['csv'],
            key="bad_responses"
        )
        
    with col2:
        st.subheader("👥 User Data Sheet")
        st.markdown("Upload the complete user data export")
        user_data_file = st.file_uploader(
            "Choose user data CSV file",
            type=['csv'],
            key="user_data"
        )
    
    # Process files if both are uploaded
    if bad_responses_file is not None and user_data_file is not None:
        try:
            # Read the CSV files
            with st.spinner("Reading uploaded files..."):
                bad_responses_df = pd.read_csv(bad_responses_file)
                user_data_df = pd.read_csv(user_data_file)
            
            st.success("✅ Files uploaded successfully!")
            
            # Display file information
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Bad Responses: {len(bad_responses_df)} rows")
                if len(bad_responses_df) > 0:
                    st.write("**Column A (User REF) Preview:**")
                    st.write(bad_responses_df.iloc[:5, 0])  # Show first 5 rows of column A
                    
            with col2:
                st.info(f"User Data: {len(user_data_df)} rows")
                if len(user_data_df) > 0:
                    st.write("**Available Columns:**")
                    st.write(list(user_data_df.columns))
            
            # Validate required columns exist
            if len(bad_responses_df.columns) == 0:
                st.error("❌ Bad responses file appears to be empty or invalid")
                return
                
            if len(user_data_df.columns) < 8:
                st.error("❌ User data file doesn't have enough columns (needs at least 8 columns: B, C, F, H)")
                return
            
            # Get column names (assuming 0-indexed, so B=1, C=2, F=5, H=7)
            bad_responses_ref_col = bad_responses_df.columns[0]  # Column A
            
            # For user data, we need to be careful about column indexing
            if len(user_data_df.columns) >= 8:
                user_ref_col = user_data_df.columns[1]    # Column B (index 1)
                email_col = user_data_df.columns[2]       # Column C (index 2)
                lucid_ref_col = user_data_df.columns[5]   # Column F (index 5)
                country_col = user_data_df.columns[7]     # Column H (index 7)
            else:
                st.error("❌ User data file doesn't have enough columns")
                return
            
            # Show column mapping
            st.subheader("🔗 Column Mapping")
            mapping_col1, mapping_col2 = st.columns(2)
            
            with mapping_col1:
                st.write("**Bad Responses:**")
                st.write(f"• User REF: `{bad_responses_ref_col}` (Column A)")
                
            with mapping_col2:
                st.write("**User Data:**")
                st.write(f"• User REF: `{user_ref_col}` (Column B)")
                st.write(f"• Email: `{email_col}` (Column C)")
                st.write(f"• Lucid Reference: `{lucid_ref_col}` (Column F)")
                st.write(f"• Country: `{country_col}` (Column H)")
            
            # Process the data merge
            with st.spinner("Processing data consolidation..."):
                # Create a copy of bad responses to avoid modifying original
                result_df = bad_responses_df.copy()
                
                # Merge the data based on User REF
                merged_data = pd.merge(
                    result_df,
                    user_data_df[[user_ref_col, email_col, lucid_ref_col, country_col]],
                    left_on=bad_responses_ref_col,
                    right_on=user_ref_col,
                    how='left'
                )
                
                # Drop the duplicate user_ref column from the merge
                if user_ref_col in merged_data.columns and user_ref_col != bad_responses_ref_col:
                    merged_data = merged_data.drop(columns=[user_ref_col])
                
                # Rename columns for clarity
                final_df = merged_data.rename(columns={
                    email_col: 'Email',
                    lucid_ref_col: 'Lucid_Reference',
                    country_col: 'Country'
                })
            
            st.success("✅ Data consolidation completed!")
            
            # Show results summary
            st.subheader("📈 Results Summary")
            
            total_bad_responses = len(bad_responses_df)
            matched_responses = final_df['Email'].notna().sum()
            unmatched_responses = total_bad_responses - matched_responses
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("Total Bad Responses", total_bad_responses)
                
            with summary_col2:
                st.metric("Successfully Matched", matched_responses)
                
            with summary_col3:
                st.metric("Unmatched", unmatched_responses)
            
            if unmatched_responses > 0:
                st.warning(f"⚠️ {unmatched_responses} User REFs from bad responses were not found in the user data")
            
            # Show preview of consolidated data
            st.subheader("👀 Data Preview")
            st.write("**First 10 rows of consolidated data:**")
            st.dataframe(final_df.head(10), use_container_width=True)
            
            # Download section
            st.subheader("💾 Download Consolidated Data")
            
            # Convert dataframe to CSV
            csv_buffer = io.StringIO()
            final_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consolidated_bad_responses_{timestamp}.csv"
            
            st.download_button(
                label="📥 Download Consolidated CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                use_container_width=True
            )
            
            st.success(f"🎉 Ready to download! The file contains {len(final_df)} rows with consolidated data.")
            
        except Exception as e:
            st.error(f"❌ An error occurred while processing the files: {str(e)}")
            st.write("Please check that:")
            st.write("• Both files are valid CSV format")
            st.write("• The bad responses file has User REF in the first column")
            st.write("• The user data file has the required columns in positions B, C, F, and H")
    
    else:
        # Instructions when no files are uploaded
        st.info("👆 Please upload both CSV files to begin data consolidation")
        
        with st.expander("📋 How to use this tool"):
            st.markdown("""
            **Step 1:** Upload your "Bad Responses" CSV file
            - This should contain User REF values in Column A
            
            **Step 2:** Upload your "User Data" CSV file  
            - User REF should be in Column B
            - Email should be in Column C
            - Lucid Reference should be in Column F
            - Country should be in Column H
            
            **Step 3:** Review the data preview and download the consolidated CSV
            - The tool will automatically match User REFs and add the required information
            - Unmatched entries will be flagged for your review
            """)

if __name__ == "__main__":
    main()

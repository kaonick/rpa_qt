from rpa_qt.tmp_fins.util_file import get_csv_files
from rpa_qt.utils.data.vo_parser import load_data

balance_sheet_dict = {
    "現金及約當現金": "Cash_and_Cash_Equivalents",
    "存放央行及拆借銀行同業": "Deposits_with_Central_Bank_and_Interbank_Borrowings",
    "透過損益按公允價值衡量之金融資產": "Financial_Assets_at_Fair_Value_through_Profit_or_Loss",
    "透過其他綜合損益按公允價值衡量之金融資產": "Financial_Assets_at_Fair_Value_through_Other_Comprehensive_Income",
    "按攤銷後成本衡量之債務工具投資": "Debt_Instruments_Measured_at_Amortized_Cost",
    "避險之衍生金融資產淨額": "Hedging_Derivative_Financial_Assets_Net",
    "附賣回票券及債券投資淨額": "Investment_in_Securities_and_Bonds_with_Repurchase_Agreements_Net",
    "應收款項－淨額": "Receivables_Net",
    "當期所得稅資產": "Current_Tax_Assets",
    "待出售資產－淨額": "Assets_Held_for_Sale_Net",
    "待分配予業主之資產－淨額": "Assets_for_Distribution_to_Owners_Net",
    "貼現及放款－淨額": "Discount_and_Loans_Net",
    "採用權益法之投資－淨額": "Equity_Method_Investments_Net",
    "受限制資產－淨額": "Restricted_Assets_Net",
    "其他金融資產－淨額": "Other_Financial_Assets_Net",
    "不動產及設備－淨額": "Property_Plant_and_Equipment_Net",
    "使用權資產－淨額": "Right_of_Use_Assets_Net",
    "投資性不動產投資－淨額": "Investment_Property_Net",
    "無形資產－淨額": "Intangible_Assets_Net",
    "遞延所得稅資產": "Deferred_Tax_Assets",
    "其他資產－淨額": "Other_Assets_Net",
    "資產總額": "Total_Assets",
    "央行及銀行同業存款": "Central_Bank_and_Interbank_Deposits",
    "央行及同業融資": "Central_Bank_and_Interbank_Financing",
    "透過損益按公允價值衡量之金融負債": "Financial_Liabilities_at_Fair_Value_through_Profit_or_Loss",
    "避險之衍生金融負債－淨額": "Hedging_Derivative_Financial_Liabilities_Net",
    "附買回票券及債券負債": "Liabilities_from_Securities_and_Bonds_with_Repurchase_Agreements",
    "應付款項": "Payables",
    "當期所得稅負債": "Current_Tax_Liabilities",
    "與待出售資產直接相關之負債": "Liabilities_Directly_Associated_with_Assets_Held_for_Sale",
    "存款及匯款": "Deposits_and_Remittances",
    "應付金融債券": "Financial_Bond_Payables",
    "應付公司債": "Corporate_Bond_Payables",
    "特別股負債": "Preferred_Stock_Liabilities",
    "其他金融負債": "Other_Financial_Liabilities",
    "負債準備": "Provisions",
    "租賃負債": "Lease_Liabilities",
    "遞延所得稅負債": "Deferred_Tax_Liabilities",
    "其他負債": "Other_Liabilities",
    "負債總額": "Total_Liabilities",
    "股本": "Capital_Stock",
    "權益─具證券性質之虛擬通貨": "Equity_Virtual_Currency_with_Securities_Nature",
    "資本公積": "Capital_Surplus",
    "保留盈餘": "Retained_Earnings",
    "其他權益": "Other_Equity",
    "庫藏股票": "Treasury_Stock",
    "歸屬於母公司業主之權益合計": "Total_Equity_Attributable_to_Parent_Company_Owners",
    "共同控制下前手權益": "Equity_of_Predecessors_under_Common_Control",
    "合併前非屬共同控制股權": "Non_Common_Control_Equity_before_Consolidation",
    "非控制權益": "Non_Controlling_Interests",
    "權益總額": "Total_Equity",
    "待註銷股本股數（單位：股）": "Shares_Pending_Cancellation_in_shares",
    "母公司暨子公司所持有之母公司庫藏股股數（單位：股）": "Number_of_Treasury_Shares_Held_by_Parent_and_Subsidiary_in_shares",
    "預收股款（權益項下）之約當發行股數（單位：股）": "Number_of_Shares_Underwritten_for_Prepayments_of_Share_Capital_in_shares",
    "每股參考淨值": "Reference_Net_Value_per_Share",
    '出表日期': 'Report_Date',
    '年度': 'Year',
    '季別': 'Quarter',
    '公司代號': 'Company_Code',
    '公司名稱': 'Company_Name',
    '流動資產': 'Current_Assets',
    '非流動資產': 'Non_Current_Assets',
    '資產總計': 'Total_Assets',
    '流動負債': 'Current_Liabilities',
    '非流動負債': 'Non_Current_Liabilities',
    '負債總計': 'Total_Liabilities',
    '權益－具證券性質之虛擬通貨': 'Equity_Virtual_Currency_with_Securities_Nature',
    '保留盈餘（或累積虧損）': 'Retained_Earnings_or_Accumulated_Losses',
    '歸屬於母公司業主權益合計': 'Total_Equity_Attributable_to_Parent_Company_Owners',
    '權益總計': 'Total_Equity',
    '母公司暨子公司持有之母公司庫藏股股數（單位：股）': 'Number_of_Treasury_Shares_Held_by_Parent_and_Subsidiary_in_shares',
    '存放央行及拆借金融同業': 'Deposits_with_Central_Bank_and_Interbank_Financing',
    '避險之衍生金融資產': 'Hedging_Derivative_Financial_Assets',
    '附賣回票券及債券投資': 'Investment_in_Securities_and_Bonds_with_Repurchase_Agreements',
    'Unnamed: 15': 'Unnamed_15',
    '再保險合約資產－淨額': 'Reinsurance_Contract_Assets_Net',
    '投資性不動產－淨額': 'Investment_Property_Net',
    '央行及金融同業存款': 'Central_Bank_and_Financial_Intermediary_Deposits',
    '避險之衍生金融負債': 'Hedging_Derivative_Financial_Liabilities',
    '應付商業本票－淨額': 'Commercial_Paper_Payables_Net',
    '應付債券': 'Bond_Payables',
    '其他借款': 'Other_Borrowings',
    '歸屬於母公司業主之權益': 'Equity_Attributable_to_Parent_Company_Owners',
    '應收款項': 'Receivables',
    '本期所得稅資產': 'Current_Tax_Assets',
    '待出售資產': 'Assets_Held_for_Sale',
    '待分配予業主之資產（或處分群組）': 'Assets_for_Distribution_to_Owners_or_Disposal_Group',
    '投資': 'Investments',
    '再保險合約資產': 'Reinsurance_Contract_Assets',
    '不動產及設備': 'Property_Plant_and_Equipment',
    '使用權資產': 'Right_of_Use_Assets',
    '無形資產': 'Intangible_Assets',
    '其他資產': 'Other_Assets',
    '分離帳戶保險商品資產': 'Separate_Account_Insurance_Product_Assets',
    '短期債務': 'Short_Term_Debt',
    '本期所得稅負債': 'Current_Tax_Liabilities',
    '保險負債': 'Insurance_Liabilities',
    '具金融商品性質之保險契約準備': 'Insurance_Contract_Reserves_of_Financial_Product_Nature',
    '外匯價格變動準備': 'Foreign_Exchange_Price_Fluctuation_Reserve',
    '分離帳戶保險商品負債': 'Separate_Account_Insurance_Product_Liabilities'
}





def read_download_csv():
    download_path = "C:/Users/n000000930/Downloads"
    csv_list = get_csv_files(download_path)

    not_include_list = []
    for csv_file in csv_list:
        print(f"csv_file={csv_file}")
        try:
            df = load_data(download_path + "/" + csv_file)
            print(df)

            columns = df.columns
            for c in columns:
                if c not in balance_sheet_dict.keys():
                    if c not in not_include_list:
                        not_include_list.append(c)
                    print(f"Error: {c} not in balance_sheet_dict.keys()")
                    continue
        except Exception as err:
            print(err)
    print(not_include_list)
if __name__ == '__main__':
    read_download_csv()
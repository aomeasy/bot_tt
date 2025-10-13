import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import Database
from bot import BitkubBot
import config

st.set_page_config(page_title="Bot Trade Dashboard", page_icon="🤖", layout="wide")

# Initialize
db = Database()
bot = BitkubBot()

# Sidebar
st.sidebar.title("🤖 Bot Trade Control")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 บันทึกราคา"):
    with st.spinner("กำลังดึงข้อมูล..."):
        if bot.save_prices():
            st.sidebar.success("✅ บันทึกราคาสำเร็จ!")
        else:
            st.sidebar.error("❌ เกิดข้อผิดพลาด")

if st.sidebar.button("💚 Health Check"):
    status = bot.health_check()
    if status['database'] == 'OK' and status['api'] == 'OK':
        st.sidebar.success("✅ ระบบทำงานปกติ")
    else:
        st.sidebar.error(f"❌ DB: {status['database']}, API: {status['api']}")

if st.sidebar.button("📊 สร้างรายงานวันนี้"):
    bot.generate_daily_report()
    st.sidebar.success("✅ สร้างรายงานแล้ว")

if st.sidebar.button("💾 Backup Database"):
    with st.spinner("กำลัง backup..."):
        bot.backup_database()
        st.sidebar.success("✅ Backup สำเร็จ")

if st.sidebar.button("🔍 วิเคราะห์ตลาด"):
    signals = bot.analyze_market()
    if signals:
        st.sidebar.success(f"พบสัญญาณ {len(signals)} รายการ")
        for sig in signals:
            st.sidebar.info(f"{sig['action']} {sig['symbol']}: {sig['reason']}")
    else:
        st.sidebar.info("ไม่พบสัญญาณเทรด")

st.sidebar.markdown("---")
st.sidebar.info(f"⚙️ Min Profit: {config.MIN_PROFIT_PERCENT}%\n💰 Max Trade: {config.MAX_TRADE_AMOUNT} THB")

# Main Dashboard
st.title("📈 Bot Trade Dashboard")
st.markdown("### ระบบเทรดอัตโนมัติด้วย Bitkub API")

# Metrics
col1, col2, col3, col4 = st.columns(4)

trades_today = db.get_trades_today()
total_profit_today = sum([t['profit'] for t in trades_today]) if trades_today else 0
success_today = sum([1 for t in trades_today if t['profit'] > 0]) if trades_today else 0
success_rate_today = (success_today / len(trades_today) * 100) if trades_today else 0

col1.metric("🔢 เทรดวันนี้", len(trades_today))
col2.metric("💰 กำไรวันนี้", f"{total_profit_today:.2f} THB", delta=f"{total_profit_today:.2f}")
col3.metric("✅ อัตราสำเร็จ", f"{success_rate_today:.1f}%")
col4.metric("🎯 เหรียญที่เทรด", len(config.SYMBOLS))

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 ภาพรวม", "💹 ราคา", "📝 เทรดวันนี้", "📈 สรุปรายเดือน"])

with tab1:
    st.subheader("📊 สรุปภาพรวม 30 วัน")
    summary = db.get_daily_summary(30)
    
    if summary:
        df_summary = pd.DataFrame(summary)
        
        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_summary['date'],
            y=df_summary['profit'],
            name='กำไร/ขาดทุน',
            marker_color=['green' if x > 0 else 'red' for x in df_summary['profit']]
        ))
        fig.update_layout(
            title='กำไร/ขาดทุนรายวัน',
            xaxis_title='วันที่',
            yaxis_title='THB',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.dataframe(df_summary, use_container_width=True)
        
        # Summary Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 กำไรรวม 30 วัน", f"{df_summary['profit'].sum():.2f} THB")
        col2.metric("📊 เทรดรวม", int(df_summary['trades'].sum()))
        col3.metric("✅ อัตราสำเร็จเฉลี่ย", f"{df_summary['success_rate'].mean():.1f}%")
    else:
        st.info("ยังไม่มีข้อมูล")

with tab2:
    st.subheader("💹 ราคาล่าสุด")
    
    symbol_select = st.selectbox("เลือกเหรียญ", config.SYMBOLS)
    hours = st.slider("แสดงข้อมูล (ชั่วโมง)", 1, 168, 24)
    
    prices = db.get_prices(symbol_select, hours)
    
    if prices:
        df_prices = pd.DataFrame(prices)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_prices['timestamp'],
            y=df_prices['price'],
            mode='lines+markers',
            name='ราคา',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title=f'กราฟราคา {symbol_select}',
            xaxis_title='เวลา',
            yaxis_title='ราคา (THB)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("ราคาล่าสุด", f"{df_prices.iloc[0]['price']:.2f}")
        col2.metric("สูงสุด", f"{df_prices['price'].max():.2f}")
        col3.metric("ต่ำสุด", f"{df_prices['price'].min():.2f}")
        col4.metric("เฉลี่ย", f"{df_prices['price'].mean():.2f}")
    else:
        st.info("ยังไม่มีข้อมูลราคา กดปุ่ม 'บันทึกราคา' ที่ Sidebar")

with tab3:
    st.subheader("📝 รายการเทรดวันนี้")
    
    if trades_today:
        df_trades = pd.DataFrame(trades_today)
        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
        
        # Color code
        df_trades['สถานะ'] = df_trades['profit'].apply(lambda x: '🟢 กำไร' if x > 0 else '🔴 ขาดทุน')
        
        st.dataframe(
            df_trades[['timestamp', 'symbol', 'side', 'price', 'amount', 'profit', 'สถานะ']],
            use_container_width=True
        )
        
        # Profit by symbol
        profit_by_symbol = df_trades.groupby('symbol')['profit'].sum().reset_index()
        
        fig = go.Figure(data=[
            go.Bar(
                x=profit_by_symbol['symbol'],
                y=profit_by_symbol['profit'],
                marker_color=['green' if x > 0 else 'red' for x in profit_by_symbol['profit']]
            )
        ])
        fig.update_layout(title='กำไร/ขาดทุนแยกตามเหรียญ', height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ยังไม่มีรายการเทรดวันนี้")

with tab4:
    st.subheader("📈 สรุปรายเดือน")
    
    daily_reports = db.get_daily_summary(90)
    
    if daily_reports:
        df_reports = pd.DataFrame(daily_reports)
        df_reports['month'] = pd.to_datetime(df_reports['date']).dt.to_period('M')
        
        monthly = df_reports.groupby('month').agg({
            'trades': 'sum',
            'profit': 'sum',
            'success_rate': 'mean'
        }).reset_index()
        
        monthly['month'] = monthly['month'].astype(str)
        
        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly['month'],
            y=monthly['profit'],
            name='กำไรรายเดือน',
            marker_color=['green' if x > 0 else 'red' for x in monthly['profit']]
        ))
        fig.update_layout(title='กำไร/ขาดทุนรายเดือน', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(monthly, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลรายเดือน")

# Footer
st.markdown("---")
st.markdown("🤖 **Bot Trade System** | พัฒนาเพื่อ Day Trade ที่สร้างรายได้ทุกวัน")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Cleanup
db.close()

import socket
import streamlit as st
import ipaddress
import pandas as pd
from io import StringIO

st.set_page_config(page_title="IP Connection Checker", page_icon="🔌")
st.title("🔌 IP Address Connection Checker")

# Adding some color to the page
st.markdown(
    """
    <style>
        .main {
            background-color: #f1f1f1;
            padding: 20px;
        }
        .sidebar .sidebar-content {
            background-color: #333;
            color: #fff;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput>div>input {
            background-color: #f1f1f1;
            color: #333;
        }
        .stTextArea>div>textarea {
            background-color: #f1f1f1;
            color: #333;
        }
        .stSlider>div>input {
            background-color: #f1f1f1;
            color: #333;
        }
        .stDataFrame {
            border: 2px solid #4CAF50;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper to detect if an IP is private or public
def get_ip_type(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return "Private" if ip_obj.is_private else "Public"
    except ValueError:
        return "Invalid"

# -----------------------------
# SINGLE IP CHECK TAB
# -----------------------------
tab1, tab2 = st.tabs(["🔍 Single IP Check", "📋 Bulk IP Check"])

with tab1:
    st.subheader("🔍 Check a Single IP Address")
    ip = st.text_input("Enter IP Address", "8.8.8.8", placeholder="e.g., 8.8.8.8")
    port_input = st.text_input("Enter Port Number (optional)", placeholder="e.g., 80")
    timeout = st.slider("Timeout (seconds)", min_value=1, max_value=10, value=3)

    if st.button("Check Connection", key="single_check"):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            st.error("❌ Invalid IP address format.", icon="🚫")
        else:
            ip_type = get_ip_type(ip)
            st.info(f"🔎 IP Type: **{ip_type}**")

            if port_input:
                try:
                    port = int(port_input)
                    if port < 1 or port > 65535:
                        raise ValueError("Invalid port number.")
                    socket.create_connection((ip, port), timeout=timeout)
                    st.success(f"✅ Connection to {ip}:{port} is established.", icon="✔️")
                except Exception as e:
                    st.error(f"❌ Connection to {ip}:{port_input} failed: {e}", icon="🚫")
            else:
                try:
                    resolved_ip = socket.gethostbyname(ip)
                    st.success(f"✅ {ip} is resolvable to {resolved_ip}.", icon="✔️")
                except Exception as e:
                    st.error(f"❌ Unable to resolve {ip}: {e}", icon="🚫")

# -----------------------------
# BULK IP CHECK TAB
# -----------------------------
with tab2:
    st.subheader("📋 Check Bulk IP Addresses")
    st.markdown("Format: `IP` or `IP:PORT`, one per line.")
    ip_list_input = st.text_area(
        "Enter IP list here:",
        height=200,
        placeholder="Examples:\n8.8.8.8:53\n1.1.1.1\n192.168.0.1:80"
    )
    timeout_bulk = st.slider("Timeout per connection (seconds)", min_value=1, max_value=10, value=3, key="bulk_timeout")

    results = []

    if st.button("Check All IPs", key="bulk_check"):
        if not ip_list_input.strip():
            st.warning("⚠️ Please enter at least one IP address.", icon="⚠️")
        else:
            ip_lines = ip_list_input.strip().split("\n")
            for line in ip_lines:
                entry = line.strip()
                if not entry:
                    continue

                if ":" in entry:
                    ip_part, port_part = entry.split(":", 1)
                else:
                    ip_part, port_part = entry, None

                ip_type = get_ip_type(ip_part)
                status = ""

                try:
                    ipaddress.ip_address(ip_part)
                except ValueError:
                    status = "❌ Invalid IP"
                else:
                    if port_part:
                        try:
                            port = int(port_part)
                            if port < 1 or port > 65535:
                                raise ValueError
                            socket.create_connection((ip_part, port), timeout=timeout_bulk)
                            status = "✅ Reachable"
                        except Exception as e:
                            status = f"❌ Failed: {e}"
                    else:
                        try:
                            resolved_ip = socket.gethostbyname(ip_part)
                            status = f"✅ Resolvable to {resolved_ip}"
                        except Exception as e:
                            status = f"❌ Unreachable: {e}"

                results.append({
                    "IP Address": ip_part,
                    "Port": port_part if port_part else "N/A",
                    "Type": ip_type,
                    "Status": status
                })

            # Display results in a colorful table
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            # Generate CSV
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name="ip_check_results.csv",
                mime="text/csv",
                key="download_button"
            )

            st.markdown("### 📄 CSV Preview")
            st.code(csv_data, language="csv")

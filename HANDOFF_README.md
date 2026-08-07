# 🌙 Handover & Continuation Guide — Oracle Cloud Deployment

**Project:** Personalized Shopping Agent  
**Date:** August 8, 2026  
**Status:** In Progress — Ready for final 1-minute resume tomorrow  

---

## 📌 VM Connection Details

- **Public IP:** `161.118.167.175`
- **Username:** `opc`
- **SSH Key Location:** `C:\Users\Lenovo\.ssh\oracle-cloud.pem`
- **OS:** Oracle Linux 9 (Always Free VM)
- **Local Workspace:** `E:\Work\Smit\Agent\Personalized-Shopping-Agent`

---

## 🚀 Tomorrow's Quick 2-Step Resume (2 Minutes)

When you return tomorrow, follow these 2 simple steps:

### Step 1: Open Port 80 in Oracle Cloud Console (60 Seconds)
1. Log in to [Oracle Cloud Console](https://cloud.oracle.com/).
2. Go to **Networking** → **Virtual Cloud Networks (VCNs)**.
3. Select your VCN → **Security Lists** → Click **Default Security List for [your-vcn]**.
4. Click **Add Ingress Rules**:
   - **Source Type:** `CIDR`
   - **Source CIDR:** `0.0.0.0/0`
   - **IP Protocol:** `TCP`
   - **Destination Port Range:** `80`
5. Click **Add Ingress Rules**.

### Step 2: Stop firewalld & Execute Deployment via SSH
1. Open PowerShell on your computer and SSH into your VM:
   ```powershell
   ssh -i "C:\Users\Lenovo\.ssh\oracle-cloud.pem" opc@161.118.167.175
   ```
   *(If SSH port 22 times out, open **Oracle Cloud Console** → **Compute** → **Instances** → **Console Connections** → **Launch Cloud Shell Connection**, log in as `opc`, and run: `sudo systemctl stop firewalld && sudo systemctl disable firewalld`)*

2. Run the deployment script on the VM:
   ```bash
   cd /home/opc
   if [ ! -d "Personalized-Shopping-Agent" ]; then
     git clone https://github.com/SaadRiaz99/Personalized-Shopping-Agent.git
   fi
   cd Personalized-Shopping-Agent
   git pull origin main
   bash deploy-oracle.sh
   ```

---

## 🌐 Application URL & Credentials

After running `bash deploy-oracle.sh`, your application will be live at:

- **Web Application URL:** **http://161.118.167.175**
- **API Health Check:** `http://161.118.167.175/api/health`

### Default Login Accounts:
| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `Admin@123` |
| **User** | `user1` | `User@1234` |

---

## 🛠️ Management & Debug Commands

Run these on your VM to manage services once deployed:

```bash
# Check service statuses
sudo systemctl status shopping-agent --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status ollama --no-pager

# View backend logs live
sudo journalctl -u shopping-agent -f

# Restart application backend
sudo systemctl restart shopping-agent

# Restart Nginx proxy
sudo systemctl restart nginx
```

---

*Sleep well! Everything is saved and ready to resume seamlessly tomorrow.*

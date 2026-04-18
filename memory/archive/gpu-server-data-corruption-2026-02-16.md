# GPU Server /data Corruption - 2026-02-16 13:45 AEDT

## Critical Issue: /data Filesystem Corrupted

**Status:** 🔴 /data mount in emergency read-only mode, I/O errors on all access attempts

### Current State

**Server:** peter@10.0.0.44 (GPU server)
**Uptime:** 1 day, 3:16 hours
**GPUs:** All healthy (RTX 3090 24GB, RTX 3080 10GB, RTX 2070 Super 8GB)

**Problem:**
```bash
$ ls /data/
ls: /data/: Input/output error
ls: reading directory '/data/': Input/output error
```

**Mount status:**
```
/dev/sdb1 /data ext4 rw,relatime,emergency_ro 0 0
                                   ^^^^^^^^^^^
                                   Emergency read-only mode
```

**Critical:** Filesystem detected corruption and remounted read-only to prevent further damage.

### What's Affected

All symlinks in `~/ai-stack/` are broken:
- `~/ai-stack/comfyui` → `/data/ai-stack/comfyui` (BROKEN)
- `~/ai-stack/ltx2` → `/data/ai-stack/ltx2` (BROKEN)
- `~/ai-stack/sadtalker` → `/data/ai-stack/sadtalker` (BROKEN)

**Impact:**
- ❌ ComfyUI inaccessible
- ❌ LTX-2 setup incomplete
- ❌ All AI models on /data inaccessible
- ❌ Cannot test LTX-2 video generation

### What's Safe

✅ **LTX-2 model file downloaded** (7.2GB in peter's home):
```
/home/peter/ltx-2-19b-distilled-lora-384.safetensors (7.2G)
```

✅ **System disk healthy** (/)
- 110.7GB total, 94GB used, 9GB free

✅ **GPUs idle and available** (no VRAM usage)

### Disk Layout

```
sda (111.8GB) - System disk (healthy)
├─ sda1 (1GB) - /boot/efi
└─ sda2 (110.7GB) - / (root)

sdb - MISSING from lsblk (was /data mount point)
  └─ sdb1 - /data (corrupted, emergency_ro)

sdc (111.8GB) - Unmounted
└─ sdc1 (111.8GB ext4) - NOT MOUNTED

sdd (931.5GB) - Unmounted (likely the USB HDD)
└─ sdd1 (931.5GB ext4) - Should be /data2 per fstab
```

### fstab Configuration

```
/dev/sdb1 /data ext4 defaults 0 2
UUID=eb82487e-089f-40e5-99ea-78c79b3836d3 /data2 ext4 defaults 0 2
```

**Note:** /data2 is configured but NOT currently mounted.

### Recovery Options

#### Option 1: Remount /data (Requires sudo)
```bash
# Check filesystem
sudo fsck -f /dev/sdb1

# If recoverable, remount
sudo mount -o remount,rw /data
```

**Risk:** May lose data if corruption is severe.

#### Option 2: Use /data2 (931.5GB USB HDD)
```bash
# Create mount point if needed
sudo mkdir -p /data2

# Mount the USB HDD
sudo mount /dev/sdd1 /data2

# Or use UUID from fstab
sudo mount UUID=eb82487e-089f-40e5-99ea-78c79b3836d3 /data2

# Move AI stack to /data2
sudo mkdir -p /data2/ai-stack
# Copy from home or re-setup
```

**Pros:** 
- 931GB space (way more than 111GB SSD)
- Fresh start, no corruption

**Cons:**
- Slower (USB HDD vs SSD)
- Need to reinstall ComfyUI or restore from backup

#### Option 3: Use sdc1 (111.8GB SSD)
```bash
# Format and mount fresh SSD
sudo mkfs.ext4 /dev/sdc1
sudo mount /dev/sdc1 /data-new
```

**Pros:** 
- Fast (SSD)
- Clean slate

**Cons:**
- Only 111GB (same as current)
- Need to reinstall everything

### Immediate Actions Needed

1. **Diagnose /data corruption** (needs sudo access):
   ```bash
   ssh peter@10.0.0.44
   sudo dmesg | grep -E 'sdb|error|I/O'
   sudo fsck -n /dev/sdb1  # Read-only check
   ```

2. **Mount /data2 for recovery**:
   ```bash
   sudo mkdir -p /data2
   sudo mount /dev/sdd1 /data2
   ls -la /data2  # Check if data exists
   ```

3. **Restore AI stack**:
   - If /data2 already has data → use it
   - If /data2 is empty → reinstall ComfyUI, move LTX-2 model
   - Update symlinks in ~/ai-stack/ to point to /data2

### LTX-2 Status: NOT READY

**Current state:**
- ✅ Model downloaded (7.2GB LoRA file in ~/peter/)
- ❌ ComfyUI inaccessible (on corrupted /data)
- ❌ Missing Gemma 3 text encoder (download blocked previously)
- ❌ Cannot test until filesystem recovered

**Blockers:**
1. /data filesystem corruption (critical)
2. Need sudo access to recover/remount
3. ComfyUI needs to be accessible
4. Gemma 3 encoder still needs download

### Recommended Recovery Path

**Phase 1: Filesystem recovery** (5-10 min)
```bash
# On GPU server (needs sudo password)
sudo mount /dev/sdd1 /data2
ls -la /data2  # Check contents
```

**Phase 2: Restore AI stack** (15-30 min)
```bash
# If /data2 empty, reinstall ComfyUI
cd /data2
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI && uv pip install -r requirements.txt

# Move LTX-2 model
mkdir -p /data2/ai-stack/comfyui/ComfyUI/models/checkpoints
mv ~/ltx-2-19b-distilled-lora-384.safetensors /data2/ai-stack/comfyui/ComfyUI/models/checkpoints/

# Update symlinks
rm ~/ai-stack/comfyui
ln -s /data2/ai-stack/comfyui ~/ai-stack/comfyui
```

**Phase 3: Download Gemma 3** (10-20 min)
```bash
# Authenticate to Hugging Face
huggingface-cli login

# Download text encoder
cd /data2/ai-stack/comfyui/ComfyUI/models/text_encoders
huggingface-cli download google/gemma-2-2b-it
```

**Phase 4: Test LTX-2** (5 min)
```bash
# Start ComfyUI
cd /data2/ai-stack/comfyui/ComfyUI
python main.py --port 8188

# Access at http://10.0.0.44:8188
# Load LTX-2 workflow and generate test video
```

### Next Steps

**Immediate (needs Bowen):**
- [ ] Provide sudo password for peter@10.0.0.44
- [ ] Decide: Recover /data or switch to /data2?

**After access granted:**
- [ ] Mount /data2 or recover /data
- [ ] Restore ComfyUI
- [ ] Complete LTX-2 setup
- [ ] Test video generation

---

**Time estimate:** 30-60 minutes total recovery time (once sudo access available)
**Severity:** HIGH (blocks all AI media generation work)
**Root cause:** Unknown (disk failure? power issue? filesystem bug?)

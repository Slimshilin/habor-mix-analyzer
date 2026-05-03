#!/bin/bash
set -euo pipefail

# Reference solution for gso task
# This script demonstrates how to solve the task

echo "Executing solution..."

apply_patch() {
    local patch_file=$1
    local applied=false
    
    # Ensure patch_file exists
    if [ ! -f "$patch_file" ]; then
        echo "Patch file does not exist: $patch_file"
        echo ">>>>> Patch Apply Failed"
        exit 1
    fi

    # reset, if any uncommited changes
    if ! git diff-index --quiet HEAD --; then
        echo "Uncommitted changes found. Resetting..."
        git reset --hard HEAD
    fi
    
    # file patterns to exclude
    local exclude_options="--exclude=.venv/* --exclude=.git/* --exclude=__pycache__/* --exclude=*.egg-info/* --exclude=*.json --exclude=*.txt --exclude=*.csv --exclude=*.log --exclude=*.pkl"

    # Try git apply with verbose output
    if git apply --verbose $exclude_options "$patch_file" 2>&1; then
        echo "Successfully applied patch using git apply --verbose"
        echo ">>>>> Applied Patch"
        applied=true
    elif git apply --verbose --ignore-space-change $exclude_options "$patch_file" 2>&1; then
        echo "Successfully applied patch using git apply --verbose --ignore-space-change"
        echo ">>>>> Applied Patch"
        applied=true
    elif git apply --verbose --ignore-space-change --reject $exclude_options "$patch_file" 2>&1; then
        echo "Successfully applied patch using git apply --verbose --ignore-space-change --reject"
        echo ">>>>> Applied Patch"
        applied=true
    elif patch --batch --fuzz=5 -p1 -i "$patch_file" 2>&1; then
        echo "Successfully applied patch using patch command"
        echo ">>>>> Applied Patch"
        applied=true
    fi

    if [ "$applied" = false ]; then
        echo "Failed to apply patch using all methods"
        echo ">>>>> Patch Apply Failed"
        exit 1
    fi
}

cat > /tmp/patch.diff << '__SOLUTION__'
diff --git a/asv_bench/benchmarks/io/csv.py b/asv_bench/benchmarks/io/csv.py
index 36301d22db..ecaad609c3 100644
--- a/asv_bench/benchmarks/io/csv.py
+++ b/asv_bench/benchmarks/io/csv.py
@@ -12,6 +12,7 @@ from pandas import (
     DataFrame,
     concat,
     date_range,
+    period_range,
     read_csv,
     to_datetime,
 )
@@ -98,24 +99,76 @@ class ToCSVDatetimeIndex(BaseIO):
         self.data.to_csv(self.fname)
 
 
+class ToCSVPeriod(BaseIO):
+    fname = "__test__.csv"
+
+    params = ([1000, 10000], ["D", "H"])
+    param_names = ["nobs", "freq"]
+
+    def setup(self, nobs, freq):
+        rng = period_range(start="2000-01-01", periods=nobs, freq=freq)
+        self.data = DataFrame(rng)
+        if freq == "D":
+            self.default_fmt = "%Y-%m-%d"
+        elif freq == "H":
+            self.default_fmt = "%Y-%m-%d %H:00"
+
+    def time_frame_period_formatting_default(self, nobs, freq):
+        self.data.to_csv(self.fname)
+
+    def time_frame_period_formatting_default_explicit(self, nobs, freq):
+        self.data.to_csv(self.fname, date_format=self.default_fmt)
+
+    def time_frame_period_formatting(self, nobs, freq):
+        # Nb: `date_format` is not actually taken into account here today, so the
+        # performance is currently identical to `time_frame_period_formatting_default`
+        # above. This timer is therefore expected to degrade when GH#51621 is fixed.
+        # (Remove this comment when GH#51621 is fixed.)
+        self.data.to_csv(self.fname, date_format="%Y-%m-%d___%H:%M:%S")
+
+
+class ToCSVPeriodIndex(BaseIO):
+    fname = "__test__.csv"
+
+    params = ([1000, 10000], ["D", "H"])
+    param_names = ["nobs", "freq"]
+
+    def setup(self, nobs, freq):
+        rng = period_range(start="2000-01-01", periods=nobs, freq=freq)
+        self.data = DataFrame({"a": 1}, index=rng)
+        if freq == "D":
+            self.default_fmt = "%Y-%m-%d"
+        elif freq == "H":
+            self.default_fmt = "%Y-%m-%d %H:00"
+
+    def time_frame_period_formatting_index(self, nobs, freq):
+        self.data.to_csv(self.fname, date_format="%Y-%m-%d___%H:%M:%S")
+
+    def time_frame_period_formatting_index_default(self, nobs, freq):
+        self.data.to_csv(self.fname)
+
+    def time_frame_period_formatting_index_default_explicit(self, nobs, freq):
+        self.data.to_csv(self.fname, date_format=self.default_fmt)
+
+
 class ToCSVDatetimeBig(BaseIO):
     fname = "__test__.csv"
     timeout = 1500
     params = [1000, 10000, 100000]
-    param_names = ["obs"]
+    param_names = ["nobs"]
 
-    def setup(self, obs):
+    def setup(self, nobs):
         d = "2018-11-29"
         dt = "2018-11-26 11:18:27.0"
         self.data = DataFrame(
             {
-                "dt": [np.datetime64(dt)] * obs,
-                "d": [np.datetime64(d)] * obs,
-                "r": [np.random.uniform()] * obs,
+                "dt": [np.datetime64(dt)] * nobs,
+                "d": [np.datetime64(d)] * nobs,
+                "r": [np.random.uniform()] * nobs,
             }
         )
 
-    def time_frame(self, obs):
+    def time_frame(self, nobs):
         self.data.to_csv(self.fname)
 
 
diff --git a/asv_bench/benchmarks/strftime.py b/asv_bench/benchmarks/strftime.py
index ac1b7f65d2..39cc82e1bd 100644
--- a/asv_bench/benchmarks/strftime.py
+++ b/asv_bench/benchmarks/strftime.py
@@ -7,58 +7,109 @@ from pandas import offsets
 class DatetimeStrftime:
     timeout = 1500
     params = [1000, 10000]
-    param_names = ["obs"]
+    param_names = ["nobs"]
 
-    def setup(self, obs):
+    def setup(self, nobs):
         d = "2018-11-29"
         dt = "2018-11-26 11:18:27.0"
         self.data = pd.DataFrame(
             {
-                "dt": [np.datetime64(dt)] * obs,
-                "d": [np.datetime64(d)] * obs,
-                "r": [np.random.uniform()] * obs,
+                "dt": [np.datetime64(dt)] * nobs,
+                "d": [np.datetime64(d)] * nobs,
+                "r": [np.random.uniform()] * nobs,
             }
         )
 
-    def time_frame_date_to_str(self, obs):
+    def time_frame_date_to_str(self, nobs):
         self.data["d"].astype(str)
 
-    def time_frame_date_formatting_default(self, obs):
+    def time_frame_date_formatting_default(self, nobs):
+        self.data["d"].dt.strftime(date_format=None)
+
+    def time_frame_date_formatting_default_explicit(self, nobs):
         self.data["d"].dt.strftime(date_format="%Y-%m-%d")
 
-    def time_frame_date_formatting_custom(self, obs):
+    def time_frame_date_formatting_custom(self, nobs):
         self.data["d"].dt.strftime(date_format="%Y---%m---%d")
 
-    def time_frame_datetime_to_str(self, obs):
+    def time_frame_datetime_to_str(self, nobs):
         self.data["dt"].astype(str)
 
-    def time_frame_datetime_formatting_default_date_only(self, obs):
+    def time_frame_datetime_formatting_default(self, nobs):
+        self.data["dt"].dt.strftime(date_format=None)
+
+    def time_frame_datetime_formatting_default_explicit_date_only(self, nobs):
         self.data["dt"].dt.strftime(date_format="%Y-%m-%d")
 
-    def time_frame_datetime_formatting_default(self, obs):
+    def time_frame_datetime_formatting_default_explicit(self, nobs):
         self.data["dt"].dt.strftime(date_format="%Y-%m-%d %H:%M:%S")
 
-    def time_frame_datetime_formatting_default_with_float(self, obs):
+    def time_frame_datetime_formatting_default_with_float(self, nobs):
         self.data["dt"].dt.strftime(date_format="%Y-%m-%d %H:%M:%S.%f")
 
-    def time_frame_datetime_formatting_custom(self, obs):
+    def time_frame_datetime_formatting_custom(self, nobs):
         self.data["dt"].dt.strftime(date_format="%Y-%m-%d --- %H:%M:%S")
 
 
+class PeriodStrftime:
+    timeout = 1500
+    params = ([1000, 10000], ["D", "H"])
+    param_names = ["nobs", "freq"]
+
+    def setup(self, nobs, freq):
+        self.data = pd.DataFrame(
+            {
+                "p": pd.period_range(start="2000-01-01", periods=nobs, freq=freq),
+                "r": [np.random.uniform()] * nobs,
+            
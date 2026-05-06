import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Spinner } from "../components/ui/spinner";
import { apiRequest } from "../lib/api";
import {
  Database, Trash2, Zap, Clock, ChevronDown, ChevronUp, Server,
  Shield, Globe, KeyRound, Eye, EyeOff
} from "lucide-react";

export default function Connect() {
  const { login, connection, fetchDefaults } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [quickLoading, setQuickLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("new");
  const [history, setHistory] = useState([]);
  const [showSSH, setShowSSH] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [defaults, setDefaults] = useState(null);

  const [formData, setFormData] = useState({
    host: "localhost",
    port: "1433",
    user: "sa",
    password: "",
    driver: "ODBC Driver 17 for SQL Server",
    useSSH: false,
    sshHost: "",
    sshPort: "22",
    sshUser: "",
    sshPassword: "",
    sshKeyFile: "",
    dockerContainer: "",
  });

  useEffect(() => {
    if (connection) {
      navigate("/dashboard");
      return;
    }
    fetchHistory();
    loadDefaults();
  }, []);

  const loadDefaults = async () => {
    const data = await fetchDefaults();
    if (data?.config) {
      setDefaults(data);
    }
  };

  const fetchHistory = async () => {
    try {
      const data = await apiRequest("/api/history", { method: "GET" });
      setHistory(data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const config = {
        host: formData.host,
        port: formData.port,
        user: formData.user,
        password: formData.password,
        driver: formData.driver,
      };

      if (formData.useSSH) {
        config.ssh = {
          host: formData.sshHost,
          port: parseInt(formData.sshPort),
          user: formData.sshUser,
          password: formData.sshPassword || undefined,
          key_file: formData.sshKeyFile || undefined,
          docker_container: formData.dockerContainer || undefined,
        };
      }

      await login(config);
      toast.success("Connected", `Successfully connected to ${config.host}`);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
      toast.error("Connection Failed", err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickConnect = async () => {
    if (!defaults?.config) return;
    setQuickLoading(true);
    setError("");
    try {
      const config = {
        host: defaults.config.host,
        port: defaults.config.port,
        user: defaults.config.user,
        password: defaults.config.password,
        driver: defaults.config.driver || "ODBC Driver 17 for SQL Server",
      };
      if (defaults.config.ssh) {
        config.ssh = defaults.config.ssh;
      }
      await login(config);
      toast.success("Connected", `Quick connected to ${config.host}`);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
      toast.error("Quick Connect Failed", err.message);
    } finally {
      setQuickLoading(false);
    }
  };

  const connectFromHistory = (config) => {
    setFormData({
      host: config.host,
      port: config.port,
      user: config.user,
      password: config.password || "",
      driver: config.driver || "ODBC Driver 17 for SQL Server",
      useSSH: !!config.ssh,
      sshHost: config.ssh?.host || "",
      sshPort: config.ssh?.port?.toString() || "22",
      sshUser: config.ssh?.user || "",
      sshPassword: config.ssh?.password || "",
      sshKeyFile: config.ssh?.key_file || "",
      dockerContainer: config.ssh?.docker_container || "",
    });
    setTab("new");
  };

  const removeHistoryItem = async (e, item) => {
    e.stopPropagation();
    try {
      if (item.id) {
        await apiRequest(`/api/history/${item.id}`, { method: "DELETE" });
      } else {
        await apiRequest(`/api/history?host=${encodeURIComponent(item.host)}&user=${encodeURIComponent(item.user)}`, { method: "DELETE" });
      }
      toast.info("Removed", "Connection removed from history");
      fetchHistory();
    } catch (err) {
      toast.error("Error", "Failed to delete connection");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5" />
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />

      <div className="relative z-10 w-full max-w-lg animate-slide-in-up">
        {/* Logo Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl gradient-primary shadow-lg shadow-primary/25 mb-4">
            <Database className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold">MSSQL Backup Manager</h1>
          <p className="text-sm text-muted-foreground mt-1">Connect to your SQL Server instance</p>
        </div>

        {/* Quick Connect */}
        {defaults?.config && (
          <div className="mb-4 animate-fade-in">
            <Button
              onClick={handleQuickConnect}
              disabled={quickLoading}
              className="w-full h-12 gradient-primary text-white font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-300 gap-2"
            >
              {quickLoading ? (
                <Spinner size="sm" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Quick Connect — {defaults.config.host}:{defaults.config.port}
            </Button>
          </div>
        )}

        <Card className="shadow-2xl shadow-black/20 border-border/50">
          <CardContent className="p-6">
            {/* Tabs */}
            <div className="flex w-full mb-6 bg-muted/50 rounded-lg p-1">
              <button
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                  tab === "new"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setTab("new")}
              >
                New Connection
              </button>
              <button
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                  tab === "history"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setTab("history")}
              >
                History ({history.length})
              </button>
            </div>

            {tab === "new" ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg animate-slide-in-up">
                    {error}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="host" className="text-xs font-medium flex items-center gap-1.5">
                      <Globe className="h-3 w-3" /> Host
                    </Label>
                    <Input id="host" name="host" value={formData.host} onChange={handleChange} required placeholder="localhost" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="port" className="text-xs font-medium flex items-center gap-1.5">
                      <Server className="h-3 w-3" /> Port
                    </Label>
                    <Input id="port" name="port" value={formData.port} onChange={handleChange} required placeholder="1433" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="user" className="text-xs font-medium flex items-center gap-1.5">
                      <Shield className="h-3 w-3" /> Username
                    </Label>
                    <Input id="user" name="user" value={formData.user} onChange={handleChange} required placeholder="sa" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-xs font-medium flex items-center gap-1.5">
                      <KeyRound className="h-3 w-3" /> Password
                    </Label>
                    <div className="relative">
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* SSH Toggle */}
                <button
                  type="button"
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full py-2"
                  onClick={() => {
                    setShowSSH(!showSSH);
                    setFormData((prev) => ({ ...prev, useSSH: !showSSH }));
                  }}
                >
                  {showSSH ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  SSH Tunnel / Remote Docker
                </button>

                {showSSH && (
                  <div className="space-y-4 border rounded-lg p-4 bg-muted/20 animate-slide-in-up">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="sshHost" className="text-xs">SSH Host</Label>
                        <Input id="sshHost" name="sshHost" value={formData.sshHost} onChange={handleChange} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="sshPort" className="text-xs">SSH Port</Label>
                        <Input id="sshPort" name="sshPort" value={formData.sshPort} onChange={handleChange} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="sshUser" className="text-xs">SSH User</Label>
                        <Input id="sshUser" name="sshUser" value={formData.sshUser} onChange={handleChange} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="sshPassword" className="text-xs">SSH Password</Label>
                        <Input id="sshPassword" name="sshPassword" type="password" value={formData.sshPassword} onChange={handleChange} placeholder="(Optional)" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="sshKeyFile" className="text-xs">SSH Key File Path</Label>
                      <Input id="sshKeyFile" name="sshKeyFile" value={formData.sshKeyFile} onChange={handleChange} placeholder="e.g. ~/.ssh/id_rsa" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="dockerContainer" className="text-xs">Docker Container Name</Label>
                      <Input id="dockerContainer" name="dockerContainer" value={formData.dockerContainer} onChange={handleChange} placeholder="e.g. mssql_server" />
                      <p className="text-[11px] text-muted-foreground">Required for backup/restore on Docker containers</p>
                    </div>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full h-11 font-semibold"
                  disabled={loading}
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <Spinner size="sm" /> Connecting...
                    </span>
                  ) : (
                    "Connect"
                  )}
                </Button>
              </form>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                {history.length === 0 ? (
                  <div className="text-center text-muted-foreground py-12">
                    <Clock className="h-10 w-10 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">No connection history</p>
                  </div>
                ) : (
                  history.map((conn) => (
                    <div
                      key={conn.id || `${conn.host}-${conn.user}`}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/30 cursor-pointer transition-all duration-200 group"
                      onClick={() => connectFromHistory(conn)}
                    >
                      <div className="min-w-0">
                        <div className="font-medium text-sm flex items-center gap-2">
                          <Database className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="truncate">{conn.nickname || `${conn.host}:${conn.port}`}</span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5 ml-5.5">
                          {conn.user}@{conn.host}:{conn.port}
                          {conn.ssh ? ` (via ${conn.ssh.host})` : ""}
                        </div>
                        {conn.last_used && (
                          <div className="text-[10px] text-muted-foreground/60 mt-0.5 ml-5.5">
                            Last used: {new Date(conn.last_used).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                        onClick={(e) => removeHistoryItem(e, conn)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-[11px] text-muted-foreground/50 mt-6">
          MSSQL Backup Manager v2.0 — Secure database management
        </p>
      </div>
    </div>
  );
}

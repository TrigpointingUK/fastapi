server {
    listen 80;
    server_name trigpointing.uk www.trigpointing.uk;

    # Allow large file uploads (photos)
    client_max_body_size 50m;

    # Health check endpoint (for ALB)
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Proxy all other requests to legacy server
    location / {
        proxy_pass http://${legacy_server_ip};  # Legacy server uses HTTP only (no TLS)
        
        # Preserve original request headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Handle redirects
        proxy_redirect off;
    }
}


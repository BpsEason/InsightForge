FROM php:8.2-fpm-alpine

# 安裝必要的擴展和系統依賴
RUN apk add --no-cache \
    curl \
    libzip-dev \
    libpng-dev \
    jpeg-dev \
    git \
    nodejs \
    npm \
    freetype-dev \
    libwebp-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j$(nproc) gd pdo_mysql zip bcmath opcache pcntl \
    && pecl install -o -f redis \
    && rm -rf /tmp/pear \
    && docker-php-ext-enable redis

WORKDIR /var/www/html

# 安裝 Composer
COPY --from=composer:latest /usr/bin/composer /usr/local/bin/composer

# 將應用程式代碼複製到容器中 (不複製 vendor 和 node_modules 以減少映像大小)
COPY . /var/www/html

# 執行 Composer install (在構建時安裝依賴)
RUN composer install --no-dev --optimize-autoloader --no-scripts

# 設置目錄權限
RUN chown -R www-data:www-data /var/www/html/storage \
    && chown -R www-data:www-data /var/www/html/bootstrap/cache \
    && chmod -R 775 /var/www/html/storage \
    && chmod -R 775 /var/www/html/bootstrap/cache

EXPOSE 9000
CMD ["php-fpm"]

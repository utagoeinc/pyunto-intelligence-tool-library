<?php
/**
 * Plugin Name: Pyunto Intelligence for WordPress
 * Plugin URI: https://i.pyunto.com/
 * Description: Integrate Pyunto Intelligence capabilities into your WordPress site
 * Version: 1.0.0
 * Author: Pyunto Intelligence
 * Author URI: https://i.pyunto.com/
 * License: GPL-2.0+
 * Text Domain: pyunto-intelligence
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

define('PYUNTO_INTELLIGENCE_VERSION', '1.0.0');
define('PYUNTO_INTELLIGENCE_PLUGIN_DIR', plugin_dir_path(__FILE__));

/**
 * The core plugin class
 */
class Pyunto_Intelligence {

    /**
     * The API key for Pyunto Intelligence
     *
     * @var string
     */
    private $api_key;

    /**
     * The Assistant ID to use
     *
     * @var string
     */
    private $assistant_id;

    /**
     * Initialize the plugin
     */
    public function __construct() {
        // Load plugin settings
        $this->load_settings();
        
        // Register shortcodes
        add_shortcode('pyunto_image_analyzer', array($this, 'image_analyzer_shortcode'));
        
        // Add admin menu
        add_action('admin_menu', array($this, 'add_admin_menu'));
        
        // Register settings
        add_action('admin_init', array($this, 'register_settings'));
    }

    /**
     * Load settings from WordPress options
     */
    private function load_settings() {
        $this->api_key = get_option('pyunto_intelligence_api_key', '');
        $this->assistant_id = get_option('pyunto_intelligence_assistant_id', '');
    }

    /**
     * Add options page to admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            'Pyunto Intelligence Settings',
            'Pyunto Intelligence',
            'manage_options',
            'pyunto-intelligence',
            array($this, 'settings_page')
        );
    }

    /**
     * Register plugin settings
     */
    public function register_settings() {
        register_setting('pyunto_intelligence_settings', 'pyunto_intelligence_api_key');
        register_setting('pyunto_intelligence_settings', 'pyunto_intelligence_assistant_id');
        
        add_settings_section(
            'pyunto_intelligence_settings_section',
            'API Configuration',
            array($this, 'settings_section_callback'),
            'pyunto-intelligence'
        );
        
        add_settings_field(
            'pyunto_intelligence_api_key',
            'API Key',
            array($this, 'api_key_field_callback'),
            'pyunto-intelligence',
            'pyunto_intelligence_settings_section'
        );
        
        add_settings_field(
            'pyunto_intelligence_assistant_id',
            'Assistant ID',
            array($this, 'assistant_id_field_callback'),
            'pyunto-intelligence',
            'pyunto_intelligence_settings_section'
        );
    }

    /**
     * Settings section description
     */
    public function settings_section_callback() {
        echo '<p>Enter your Pyunto Intelligence API credentials below. You can obtain these from your <a href="https://a.pyunto.com/" target="_blank">Pyunto Intelligence Dashboard</a>.</p>';
    }

    /**
     * API Key field callback
     */
    public function api_key_field_callback() {
        $api_key = get_option('pyunto_intelligence_api_key', '');
        echo '<input type="password" id="pyunto_intelligence_api_key" name="pyunto_intelligence_api_key" value="' . esc_attr($api_key) . '" class="regular-text">';
    }

    /**
     * Assistant ID field callback
     */
    public function assistant_id_field_callback() {
        $assistant_id = get_option('pyunto_intelligence_assistant_id', '');
        echo '<input type="text" id="pyunto_intelligence_assistant_id" name="pyunto_intelligence_assistant_id" value="' . esc_attr($assistant_id) . '" class="regular-text">';
    }

    /**
     * Settings page HTML
     */
    public function settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            <form action="options.php" method="post">
                <?php
                settings_fields('pyunto_intelligence_settings');
                do_settings_sections('pyunto-intelligence');
                submit_button('Save Settings');
                ?>
            </form>
        </div>
        <?php
    }

    /**
     * Image analyzer shortcode
     *
     * @param array $atts Shortcode attributes
     * @return string Shortcode output
     */
    public function image_analyzer_shortcode($atts) {
        // If no API key or Assistant ID, show error
        if (empty($this->api_key) || empty($this->assistant_id)) {
            return '<div class="pyunto-error">Pyunto Intelligence is not configured. Please set up the API key and Assistant ID in the settings.</div>';
        }
        
        // Parse attributes
        $atts = shortcode_atts(
            array(
                'upload_text' => 'Upload an image to analyze',
                'analyze_text' => 'Analyze Image',
                'max_size' => 5, // Maximum file size in MB
            ),
            $atts,
            'pyunto_image_analyzer'
        );
        
        // Enqueue necessary scripts
        wp_enqueue_script('jquery');
        wp_enqueue_media();
        
        // Generate unique ID for this instance
        $instance_id = 'pyunto-analyzer-' . wp_rand();
        
        // Start output buffer
        ob_start();
        ?>
        <div id="<?php echo esc_attr($instance_id); ?>" class="pyunto-intelligence-analyzer">
            <div class="pyunto-upload-container">
                <p><?php echo esc_html($atts['upload_text']); ?></p>
                <input type="file" class="pyunto-file-input" accept="image/*">
                <div class="pyunto-preview-container" style="display:none;">
                    <img class="pyunto-preview-image" src="">
                </div>
                <button class="pyunto-analyze-button button button-primary"><?php echo esc_html($atts['analyze_text']); ?></button>
            </div>
            <div class="pyunto-results-container" style="display:none;">
                <h3>Analysis Results</h3>
                <div class="pyunto-results-content"></div>
            </div>
            <div class="pyunto-loading" style="display:none;">Analyzing image...</div>
            <div class="pyunto-error" style="display:none;"></div>
        </div>
        <script>
            jQuery(document).ready(function($) {
                const $container = $('#<?php echo esc_js($instance_id); ?>');
                const $fileInput = $container.find('.pyunto-file-input');
                const $previewContainer = $container.find('.pyunto-preview-container');
                const $previewImage = $container.find('.pyunto-preview-image');
                const $analyzeButton = $container.find('.pyunto-analyze-button');
                const $resultsContainer = $container.find('.pyunto-results-container');
                const $resultsContent = $container.find('.pyunto-results-content');
                const $loading = $container.find('.pyunto-loading');
                const $error = $container.find('.pyunto-error');
                
                let imageFile = null;
                
                $fileInput.on('change', function(e) {
                    const file = e.target.files[0];
                    if (!file) return;
                    
                    // Check file size
                    const maxSize = <?php echo intval($atts['max_size']); ?> * 1024 * 1024; // Convert to bytes
                    if (file.size > maxSize) {
                        $error.text(`File is too large. Maximum size is ${<?php echo intval($atts['max_size']); ?>}MB`).show();
                        return;
                    }
                    
                    // Check file type
                    if (!file.type.match('image.*')) {
                        $error.text('Please select an image file').show();
                        return;
                    }
                    
                    // Hide error if any
                    $error.hide();
                    
                    // Store file for later use
                    imageFile = file;
                    
                    // Show preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        $previewImage.attr('src', e.target.result);
                        $previewContainer.show();
                    };
                    reader.readAsDataURL(file);
                });
                
                $analyzeButton.on('click', function() {
                    if (!imageFile) {
                        $error.text('Please select an image first').show();
                        return;
                    }
                    
                    // Hide error and show loading
                    $error.hide();
                    $loading.show();
                    
                    // Convert file to base64
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const base64Data = e.target.result.split(',')[1]; // Remove data URL prefix
                        
                        // Send to WordPress backend
                        $.ajax({
                            url: '<?php echo admin_url('admin-ajax.php'); ?>',
                            type: 'POST',
                            data: {
                                action: 'pyunto_analyze_image',
                                nonce: '<?php echo wp_create_nonce('pyunto_analyze_image'); ?>',
                                image_data: base64Data,
                                mime_type: imageFile.type
                            },
                            success: function(response) {
                                $loading.hide();
                                if (response.success) {
                                    // Display results
                                    $resultsContent.html('');
                                    
                                    // Format the JSON response
                                    const resultData = response.data;
                                    const $resultTable = $('<table class="pyunto-results-table"></table>');
                                    
                                    // Add headers and data
                                    $.each(resultData, function(key, value) {
                                        const $row = $('<tr></tr>');
                                        $row.append($('<th></th>').text(key));
                                        $row.append($('<td></td>').text(JSON.stringify(value)));
                                        $resultTable.append($row);
                                    });
                                    
                                    $resultsContent.append($resultTable);
                                    $resultsContainer.show();
                                } else {
                                    $error.text(response.data.message || 'An unknown error occurred').show();
                                }
                            },
                            error: function() {
                                $loading.hide();
                                $error.text('Failed to communicate with the server').show();
                            }
                        });
                    };
                    reader.readAsDataURL(imageFile);
                });
            });
        </script>
        <style>
            .pyunto-intelligence-analyzer {
                max-width: 100%;
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 5px;
            }
            .pyunto-preview-container {
                margin: 10px 0;
                max-width: 300px;
            }
            .pyunto-preview-image {
                max-width: 100%;
                height: auto;
            }
            .pyunto-analyze-button {
                margin: 10px 0;
            }
            .pyunto-results-container {
                margin-top: 20px;
                padding: 15px;
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .pyunto-results-table {
                width: 100%;
                border-collapse: collapse;
            }
            .pyunto-results-table th, 
            .pyunto-results-table td {
                padding: 8px;
                border: 1px solid #ddd;
                text-align: left;
            }
            .pyunto-results-table th {
                background: #f2f2f2;
                width: 30%;
            }
            .pyunto-loading {
                margin: 10px 0;
                padding: 10px;
                background: #e0f7fa;
                border-radius: 4px;
            }
            .pyunto-error {
                margin: 10px 0;
                padding: 10px;
                background: #ffebee;
                color: #c62828;
                border-radius: 4px;
            }
        </style>
        <?php
        return ob_get_clean();
    }
}

// Initialize the plugin
$pyunto_intelligence_plugin = new Pyunto_Intelligence();

/**
 * AJAX handler for image analysis
 */
function pyunto_ajax_analyze_image() {
    // Check nonce
    if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'pyunto_analyze_image')) {
        wp_send_json_error(array('message' => 'Security check failed'));
    }
    
    // Check for required data
    if (!isset($_POST['image_data']) || !isset($_POST['mime_type'])) {
        wp_send_json_error(array('message' => 'Missing required data'));
    }
    
    // Get API credentials
    $api_key = get_option('pyunto_intelligence_api_key', '');
    $assistant_id = get_option('pyunto_intelligence_assistant_id', '');
    
    if (empty($api_key) || empty($assistant_id)) {
        wp_send_json_error(array('message' => 'Pyunto Intelligence is not configured'));
    }
    
    // Prepare request to Pyunto Intelligence API
    $request_data = array(
        'assistantId' => $assistant_id,
        'type' => 'image',
        'data' => $_POST['image_data'],
        'mimeType' => $_POST['mime_type']
    );
    
    // Send request to API
    $response = wp_remote_post('https://a.pyunto.com/api/i/v1', array(
        'headers' => array(
            'Authorization' => 'Bearer ' . $api_key,
            'Content-Type' => 'application/json'
        ),
        'body' => json_encode($request_data),
        'timeout' => 60, // Allow up to 60 seconds for the API to respond
        'data_format' => 'body'
    ));
    
    // Check for error
    if (is_wp_error($response)) {
        wp_send_json_error(array('message' => $response->get_error_message()));
    }
    
    // Get response body
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    // Check for API error
    if (isset($data['error'])) {
        wp_send_json_error(array('message' => $data['error']['message']));
    }
    
    // Return the data
    wp_send_json_success($data);
}
add_action('wp_ajax_pyunto_analyze_image', 'pyunto_ajax_analyze_image');
add_action('wp_ajax_nopriv_pyunto_analyze_image', 'pyunto_ajax_analyze_image');
